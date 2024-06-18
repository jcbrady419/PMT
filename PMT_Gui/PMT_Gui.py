# Import necessary libraries
import sys
import os
import json
import shutil
import subprocess  # Import subprocess module
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt  # Import Qt module for alignment
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QApplication, QMessageBox, QInputDialog, QVBoxLayout, QPushButton, QWidget, QDesktopWidget, QHBoxLayout, QSpacerItem, QSizePolicy, QLabel

# Define constants for file paths
BASE_DIRECTORY_PATH = "C:/Autodesk/Autodesk_Maya_2024_1_Update_Windows_64bit_dlm"
PROJECTS_FOLDER = "PMT_Projects"
COMPANY_NAME = "Company Name"

# Create the QApplication instance
app = QApplication(sys.argv)

# Define a mixin class to center windows on the screen
class CenteredWindowMixin:
    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

class MainWindow(QMainWindow, CenteredWindowMixin):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Main Menu")
        self.setGeometry(100, 100, 400, 300)
        self.check_create_company_folder()  # Ensure the company folder and subfolders exist
        self.check_maya_installation()
        self.check_unreal_installation()
        self.initUI()
        self.center_window()
        self.json_file_path = self.create_pmt_json()  # Create/update the JSON file on startup and get its path
        self.copy_shelf_script()  # Copy the MEL script to Maya shelves directory

    def check_maya_installation(self):
        possible_paths = [
            "C:/Program Files/Autodesk/Maya2024/bin/maya.exe",
            "D:/Program Files/Autodesk/Maya2024/bin/maya.exe",
        ]
        maya_installed = any(os.path.exists(path) for path in possible_paths)
        if not maya_installed:
            QMessageBox.critical(self, "Maya 2024 Not Found", "Maya 2024 is required but not found on this computer. Please install it to proceed.")
            sys.exit(1)

    def check_unreal_installation(self):
        possible_paths = [
            "C:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor.exe",
            "D:/Program Files/Epic Games/UE_5.3/Engine/Binaries/Win64/UnrealEditor.exe",
        ]
        unreal_installed = any(os.path.exists(path) for path in possible_paths)
        if not unreal_installed:
            QMessageBox.critical(self, "Unreal Engine 5.3 Not Found", "Unreal Engine 5.3 is required but not found on this computer. Please install it to proceed.")
            sys.exit(1)

    def initUI(self):
        layout = QVBoxLayout()

        self.createprojbtn = QPushButton("Create Project")
        self.createprojbtn.clicked.connect(self.createproject)
        layout.addWidget(self.createprojbtn)

        self.editprojbtn = QPushButton("Edit Project")
        self.editprojbtn.clicked.connect(self.editproject)
        layout.addWidget(self.editprojbtn)

        assets_button = QPushButton('Department Assets')
        assets_button.setFixedSize(160, 30)
        assets_button.clicked.connect(self.open_department_assets_window)
        layout.addWidget(assets_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def copy_shelf_script(self):
        # Get the user's Documents directory
        documents_dir = os.path.join(os.path.expanduser('~'), 'OneDrive - University of Central Florida', 'Documents')
        maya_prefs_dir = os.path.join(documents_dir, 'maya', '2024', 'prefs', 'shelves')
    
        if not os.path.exists(maya_prefs_dir):
            QMessageBox.critical(self, "Error", f"Maya shelves directory does not exist at {maya_prefs_dir}!")
            return

        # Define the source and destination paths for the MEL script
        source_script_path = os.path.join(os.path.dirname(__file__), 'shelf_AutoExport.mel')
        destination_script_path = os.path.join(maya_prefs_dir, 'shelf_AutoExport.mel')

        # Copy the MEL script
        try:
            shutil.copy(source_script_path, destination_script_path)
            print(f"Copied {source_script_path} to {destination_script_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy MEL script: {e}")

    def open_department_assets_window(self, copy_source_path=None):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        self.close()
        if not os.path.exists(department_assets_path):
            try:
                os.makedirs(department_assets_path)
                print("Created 'Department Assets' folder.")
            except OSError as e:
                print(f"Error creating 'Department Assets' folder: {e}")

        if copy_source_path:
            try:
                shutil.copy(copy_source_path, department_assets_path)
                QMessageBox.information(self, "File Copied", "Maya file copied to Department Assets folder successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy Maya file to Department Assets folder: {e}")
        else:
            department_assets_window = DepartmentAssetsWindow(parent=self)
            department_assets_window.show()

    def createproject(self):
        try:
            project_name, ok = QInputDialog.getText(self, 'Project Name', 'Enter project name:')
            if not ok or not project_name:
                return

            project_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "PMT Projects", project_name)
            subdirectories = [
                'Exported/Characters',
                'Exported/Environments',
                'Exported/Props',
                'Source/Characters',
                'Source/Environments',
                'Source/Props'
            ]

            os.makedirs(project_path, exist_ok=True)
            for subdirectory in subdirectories:
                subdirectory_path = os.path.join(project_path, subdirectory)
                os.makedirs(subdirectory_path, exist_ok=True)
                if subdirectory.startswith('Source'):
                    tools_folder_path = os.path.join(subdirectory_path, 'Tools')
                    temp_folder_path = os.path.join(subdirectory_path, 'Temp')
                    config_folder_path = os.path.join(tools_folder_path, 'Config')
                    os.makedirs(tools_folder_path, exist_ok=True)
                    os.makedirs(temp_folder_path, exist_ok=True)
                    os.makedirs(config_folder_path, exist_ok=True)
                    config_json_path = os.path.join(config_folder_path, 'ConfigInfo.json')
                    if not os.path.exists(config_json_path):
                        shutil.copy(self.json_file_path, config_folder_path)  # Copy JSON file to Config folder

                                    # Copy PMT Export Tool to Tools folder
                    source_tool_path = os.path.join(os.path.dirname(__file__), 'PMT Export Tool.txt')
                    destination_tool_path = os.path.join(tools_folder_path, 'PMT Export Tool.txt')
                    if os.path.exists(source_tool_path):
                        shutil.copy(source_tool_path, destination_tool_path)
                    else:
                        QMessageBox.warning(self, "Warning", f"PMT Export Tool.txt not found at {source_tool_path}")


            source_maya_files = [
                os.path.join(project_path, 'Source/Characters/Character.ma'),
                os.path.join(project_path, 'Source/Environments/Environment.ma'),
                os.path.join(project_path, 'Source/Props/Prop.ma')
            ]
            for maya_file in source_maya_files:
                with open(maya_file, 'w') as file:
                    file.write("//Maya ASCII 2023 scene\n")

            QMessageBox.information(self, "Project Creation", f"Created project structure!")

        except OSError as e:
            QMessageBox.critical(self, "Error", f"OS error: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create project: {e}")

    def check_create_company_folder(self):
        company_folder_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME)
        pmt_projects_path = os.path.join(company_folder_path, "PMT Projects")
        department_assets_path = os.path.join(company_folder_path, "Department Assets")
        tools_folder_path = os.path.join(department_assets_path, 'Tools')
        config_folder_path = os.path.join(tools_folder_path, 'Config')
        temp_folder_department_assets_path = os.path.join(department_assets_path, 'Temp')
        temp_folder_project_assets_path = os.path.join(pmt_projects_path, "Project Assets", 'Temp')

        paths_to_create = [
            company_folder_path,
            pmt_projects_path,
            department_assets_path,
            tools_folder_path,
            config_folder_path,
            temp_folder_department_assets_path,  # Add Temp folder in Department Assets path
            temp_folder_project_assets_path     # Add Temp folder in Project Assets path
        ]

        # Create folders for Department Assets
        for path in paths_to_create:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                    print(f"Created '{path}' folder.")
                except OSError as e:
                    print(f"Error creating '{path}' folder: {e}")

        # Create JSON file in Department Assets Tools Config folder if it doesn't exist
        json_file_path_department_assets = os.path.join(config_folder_path, 'ConfigInfo.json')
        if not os.path.exists(json_file_path_department_assets):
            self.create_pmt_json(json_file_path_department_assets)

        # Copy JSON file to Project Assets Tools Config folder
        project_assets_config_path = os.path.join(pmt_projects_path, "Project Assets", 'Tools', 'Config')
        if not os.path.exists(project_assets_config_path):
            os.makedirs(project_assets_config_path)

        # Specify the path where the JSON file should be copied in the Project Assets Tools Config folder
        json_file_path_project_assets = os.path.join(project_assets_config_path, 'ConfigInfo.json')

        # Copy the JSON file from Department Assets to Project Assets
        shutil.copy(json_file_path_department_assets, json_file_path_project_assets)

        # Create folders for Project Assets
        project_assets_path = os.path.join(pmt_projects_path, "Project Assets")
        tools_folder_project_assets_path = os.path.join(project_assets_path, 'Tools')
        config_folder_project_assets_path = os.path.join(tools_folder_project_assets_path, 'Config')

        paths_to_create_project_assets = [
            project_assets_path,
            tools_folder_project_assets_path,
            config_folder_project_assets_path
        ]

        for path in paths_to_create_project_assets:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                    print(f"Created '{path}' folder.")
                except OSError as e:
                    print(f"Error creating '{path}' folder: {e}")

    def editproject(self):
        projects_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "PMT Projects")
        if not os.path.exists(projects_path):
            QMessageBox.critical(self, "Error", f"'PMT Projects' folder does not exist!")
            return
        self.project_selection_window = ProjectSelectionWindow(projects_path, previous_window=self)
        self.project_selection_window.show()
        self.close()

    def create_pmt_json(self, json_path=None):
        projects_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "PMT Projects")
        tools_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets", "Tools")
        config_path = os.path.join(tools_path, 'Config')

        if json_path is None:
            json_path = os.path.join(config_path, 'ConfigInfo.json')

        if os.path.exists(json_path):
            print(f"JSON file already exists at {json_path}")
            return json_path

        if not os.path.exists(tools_path):
            os.makedirs(tools_path)
            print(f"Created 'Tools' folder at {tools_path}")

        if not os.path.exists(config_path):
            os.makedirs(config_path)
            print(f"Created 'Config' folder at {config_path}")

        def get_folder_structure(folder_path):
            structure = {}
            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if d not in ['Tools', 'Temp']]
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    structure[name] = get_folder_structure(dir_path)
                structure["files"] = [f for f in files if f.endswith(('.ma', '.mb'))]
                break
            return structure

        folder_structure = get_folder_structure(projects_path)

        # Define the static structure description
        structure_description = {
            "Company Name": COMPANY_NAME,
            "Structure": {
                "Department Assets": {},
                "PMT Projects": {
                    "Project Assets": {},
                    "Project Name": {
                        "Characters": {},
                        "Environment": {},
                        "Props": {}
                    }
                }
            }
        }

        # Combine the static structure description with the dynamic folder structure
        output_data = {
            "Software Required": [
                "Maya 2024",
                "Unreal 5.3"
            ],
            "Structure Description": structure_description,
            "Projects": folder_structure
        }

        with open(json_path, 'w') as json_file:
            json.dump(output_data, json_file, indent=4)

        print(f"Created JSON file at {json_path}")
        return json_path

class DepartmentAssetsWindow(QMainWindow, CenteredWindowMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Department Assets")
        self.setGeometry(100, 100, 400, 300)
        self.parent = parent
        self.initUI()
        self.center_window()  # Center the window after initialization

    def initUI(self):
        layout = QVBoxLayout()

        # List Maya files in the Department Assets folder
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        maya_files = [f for f in os.listdir(department_assets_path) if f.endswith('.ma') or f.endswith('.mb')]

        for file in maya_files:
            file_layout = QVBoxLayout()

            file_button = QPushButton(file)
            file_button.clicked.connect(lambda _, f=file: self.open_maya_file(f))
            file_layout.addWidget(file_button)

            button_layout = QHBoxLayout()

            rename_button = QPushButton('Rename')
            rename_button.setFixedSize(80, 30)
            rename_button.clicked.connect(lambda _, f=file: self.rename_maya_file(f))
            button_layout.addWidget(rename_button)

            delete_button = QPushButton('Delete')
            delete_button.setFixedSize(80, 30)
            delete_button.clicked.connect(lambda _, f=file: self.delete_maya_file(f))
            button_layout.addWidget(delete_button)

            copy_button = QPushButton('Copy')
            copy_button.setFixedSize(80, 30)
            copy_button.clicked.connect(lambda _, f=file: self.copy_maya_file(f))  # Connect to the copy method
            button_layout.addWidget(copy_button)

            file_layout.addLayout(button_layout)

            layout.addLayout(file_layout)

        # Create Maya File button
        create_button = QPushButton('Create Maya File')
        create_button.setFixedSize(120, 30)
        create_button.clicked.connect(self.create_maya_file)
        layout.addWidget(create_button)

        back_button = QPushButton('Back')
        back_button.setFixedSize(60, 30)
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Create the "Tools" folder if it doesn't exist
        self.create_tools_folder()

    def create_tools_folder(self):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        tools_folder_path = os.path.join(department_assets_path, "Tools")
        if not os.path.exists(tools_folder_path):
            os.makedirs(tools_folder_path)

    def open_maya_file(self, file_name):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        file_path = os.path.join(department_assets_path, file_name)
        maya_executable = "C:/Program Files/Autodesk/Maya2024/bin/maya.exe"
        try:
            subprocess.Popen([maya_executable, file_path])
            QApplication.instance().quit()  # Exit the application after launching Maya
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Maya file: {e}")

    def rename_maya_file(self, file_name):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        old_file_path = os.path.join(department_assets_path, file_name)
        new_file_name, ok = QInputDialog.getText(self, 'Rename Maya File', 'Enter new file name:', text=file_name)
        if ok and new_file_name:
            new_file_path = os.path.join(department_assets_path, new_file_name)
            try:
                os.rename(old_file_path, new_file_path)
                QMessageBox.information(self, "File Renamed", f"Renamed file to {new_file_name}")
                self.initUI()  # Refresh the UI to reflect the renamed file
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename file: {e}")

    def delete_maya_file(self, file_name):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        file_path = os.path.join(department_assets_path, file_name)
        reply = QMessageBox.question(self, 'Delete Maya File', f"Are you sure you want to delete the file '{file_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                QMessageBox.information(self, "File Deleted", f"Deleted file '{file_name}'")
                self.initUI()  # Refresh the UI after successful deletion
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")

    def go_back(self):
        if self.parent:
            self.parent.show()
        self.close()

    def create_maya_file(self):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        file_name, ok = QInputDialog.getText(self, 'Create Maya File', 'Enter Maya file name:')
        if ok and file_name:
            file_path = os.path.join(department_assets_path, file_name + '.ma')
            try:
                with open(file_path, 'w') as file:
                    file.write("//Maya ASCII 2023 scene\n")  # Header for a basic Maya ASCII file
                QMessageBox.information(self, "File Creation", f"Created Maya file: {file_name}")
                self.open_maya_file_and_exit(file_path)  # Open the new Maya file and exit the application
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create Maya file: {e}")

    def open_maya_file_and_exit(self, file_path):
        maya_executable = "C:/Program Files/Autodesk/Maya2024/bin/maya.exe"
        try:
            subprocess.Popen([maya_executable, file_path])
            QApplication.instance().quit()  # Exit the application after launching Maya
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Maya file: {e}")

    def copy_maya_file(self, file_name):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        source_file_path = os.path.join(department_assets_path, file_name)
        self.project_selection_window = ProjectSelectionWindow(os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "PMT Projects"),
                                                               copy_source_path=source_file_path,
                                                               previous_window=self)
        self.project_selection_window.show()
        self.close()

class ProjectSelectionWindow(QWidget, CenteredWindowMixin):
    def __init__(self, projects_path, previous_window=None, copy_source_path=None):
        super().__init__()
        self.setWindowTitle('Select Project')
        self.setGeometry(100, 100, 400, 300)
        self.projects_path = projects_path
        self.previous_window = previous_window
        self.copy_source_path = copy_source_path
        self.initUI()
        self.create_project_assets_folder()
        self.center_window()

    def create_project_assets_folder(self):
        project_assets_path = os.path.join(self.projects_path, 'Project Assets')
        tools_folder_path = os.path.join(project_assets_path, 'Tools')
        department_tools_path = os.path.join('C:/Autodesk/Autodesk_Maya_2024_1_Update_Windows_64bit_dlm', 'Company name', 'Department Assets', 'Tools')

        if not os.path.exists(project_assets_path):
            os.makedirs(project_assets_path)

        if not os.path.exists(tools_folder_path):
            os.makedirs(tools_folder_path)

        if not os.path.exists(department_tools_path):
            os.makedirs(department_tools_path)

        # Copy the PMT Export Tool.txt file to the Tools folder within Project Assets
        source_tool_path = os.path.join(os.path.dirname(__file__), 'PMT Export Tool.txt')
        destination_tool_path_project = os.path.join(tools_folder_path, 'PMT Export Tool.txt')
        destination_tool_path_department = os.path.join(department_tools_path, 'PMT Export Tool.txt')
        
        try:
            shutil.copy(source_tool_path, destination_tool_path_project)
            shutil.copy(source_tool_path, destination_tool_path_department)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy export tool: {e}")

    def initUI(self):
        layout = QVBoxLayout()
        project_dirs = [d for d in os.listdir(self.projects_path) 
                        if os.path.isdir(os.path.join(self.projects_path, d)) 
                        and d not in ['Project Assets', 'Tools']]

        for project in project_dirs:
            vbox = QVBoxLayout()

            project_button = QPushButton(project)
            project_button.clicked.connect(self.project_button_clicked)
            vbox.addWidget(project_button)

            hbox = QHBoxLayout()
            rename_button = QPushButton('Rename')
            rename_button.setFixedSize(80, 30)
            rename_button.clicked.connect(lambda _, p=project: self.rename_project(p))
            hbox.addWidget(rename_button)

            delete_button = QPushButton('Delete')
            delete_button.setFixedSize(80, 30)
            delete_button.clicked.connect(lambda _, p=project: self.delete_project(p))
            hbox.addWidget(delete_button)

            vbox.addLayout(hbox)

            layout.addLayout(vbox)

        spacer_item = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer_item)

        assets_button = QPushButton('Project Assets')
        assets_button.setFixedSize(120, 30)
        assets_button.clicked.connect(self.project_assets_button_clicked)
        layout.addWidget(assets_button)

        back_button = QPushButton('Back')
        back_button.setFixedSize(60, 30)
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def project_button_clicked(self):
        sender = self.sender()
        project_path = os.path.join(self.projects_path, sender.text())

        if self.copy_source_path:
            self.copy_maya_file_to_project(project_path)
        else:
            self.maya_file_options_window = MayaFileOptionsWindow(project_path, previous_window=self)
            self.maya_file_options_window.show()
            self.close()

    def rename_project(self, project):
        old_project_path = os.path.join(self.projects_path, project)
        new_project_name, ok = QInputDialog.getText(self, 'Rename Project', 'Enter new project name:', text=project)
        if ok and new_project_name:
            new_project_path = os.path.join(self.projects_path, new_project_name)
            try:
                os.rename(old_project_path, new_project_path)
                QMessageBox.information(self, "Project Renamed", f"Renamed project to {new_project_name}")
                self.previous_window.show()
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename project: {e}")

    def delete_project(self, project):
        project_path = os.path.join(self.projects_path, project)
        reply = QMessageBox.question(self, 'Delete Project', f"Are you sure you want to delete the project '{project}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                shutil.rmtree(project_path)
                QMessageBox.information(self, "Project Deleted", f"Deleted project '{project}'")
                self.go_back()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete project: {e}")

    def copy_maya_file_to_project(self, project_path):
        source_folder = os.path.join(project_path, 'Source')
        subfolders = [f for f in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, f))]
        if not subfolders:
            QMessageBox.warning(self, "No Subfolders", "There are no subfolders in the 'Source' folder of this project.")
            return

        dialog = QInputDialog()
        dialog.setWindowTitle("Select Subfolder")
        dialog.setLabelText("Choose a subfolder within 'Source':")
        dialog.setComboBoxItems(subfolders)
        dialog.setComboBoxEditable(False)
        dialog.setOkButtonText("Copy")
        dialog.setCancelButtonText("Cancel")

        if dialog.exec_():
            selected_subfolder = dialog.textValue()
            destination_path = os.path.join(source_folder, selected_subfolder, os.path.basename(self.copy_source_path))
            try:
                shutil.copy(self.copy_source_path, destination_path)
                QMessageBox.information(self, "File Copied", "Maya file copied to subfolder successfully!")
                self.close()
                self.previous_window.show()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy Maya file to subfolder: {e}")

    def project_assets_button_clicked(self):
        project_assets_path = os.path.join(self.projects_path, 'Project Assets')

        if self.copy_source_path:
            try:
                shutil.copy(self.copy_source_path, project_assets_path)
                QMessageBox.information(self, "File Copied", "Maya file copied to Project Assets folder successfully!")
                self.go_back()  # Go back to the previous window after copying the file
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy Maya file to Project Assets folder: {e}")
        else:
            self.project_assets_window = ProjectAssetsWindow(project_assets_path, self)
            self.project_assets_window.show()
            self.close()

    def go_back(self):
        self.previous_window.show()
        self.close()

class ProjectAssetsWindow(QWidget, CenteredWindowMixin):
    def __init__(self, project_assets_path, previous_window=None):
        super().__init__()
        self.setWindowTitle('Project Assets')
        self.setGeometry(100, 100, 400, 300)
        self.project_assets_path = project_assets_path
        self.previous_window = previous_window  # Reference to the previous window
        self.initUI()
        self.center_window()

    def initUI(self):
        layout = QVBoxLayout()

        # List Maya files in the Project Assets folder
        maya_files = [f for f in os.listdir(self.project_assets_path) if f.endswith('.ma') or f.endswith('.mb')]

        for file in maya_files:
            file_layout = QVBoxLayout()

            file_button = QPushButton(file)
            file_button.clicked.connect(lambda _, f=file: self.open_maya_file(f))
            file_layout.addWidget(file_button)

            button_layout = QHBoxLayout()

            rename_button = QPushButton('Rename')
            rename_button.setFixedSize(80, 30)
            rename_button.clicked.connect(lambda _, f=file: self.rename_maya_file(f))
            button_layout.addWidget(rename_button)

            delete_button = QPushButton('Delete')
            delete_button.setFixedSize(80, 30)
            delete_button.clicked.connect(lambda _, f=file: self.delete_maya_file(f))
            button_layout.addWidget(delete_button)

            copy_button = QPushButton('Copy')
            copy_button.setFixedSize(80, 30)
            copy_button.clicked.connect(lambda _, f=file: self.copy_maya_file(f))  # Connect to the copy method
            button_layout.addWidget(copy_button)

            file_layout.addLayout(button_layout)

            layout.addLayout(file_layout)

        # Create Maya File button
        create_button = QPushButton('Create Maya File')
        create_button.setFixedSize(120, 30)
        create_button.clicked.connect(self.create_maya_file)
        layout.addWidget(create_button)

        back_button = QPushButton('Back')
        back_button.setFixedSize(60, 30)
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        container = QWidget()
        container.setLayout(layout)
        self.setLayout(layout)

    def open_maya_file(self, file_name):
        file_path = os.path.join(self.project_assets_path, file_name)
        maya_executable = "C:/Program Files/Autodesk/Maya2024/bin/maya.exe"
        try:
            subprocess.Popen([maya_executable, file_path])
            QApplication.instance().quit()  # Exit the application after launching Maya
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Maya file: {e}")

    def rename_maya_file(self, file_name):
        old_file_path = os.path.join(self.project_assets_path, file_name)
        new_file_name, ok = QInputDialog.getText(self, 'Rename Maya File', 'Enter new file name:', text=file_name)
        if ok and new_file_name:
            new_file_path = os.path.join(self.project_assets_path, new_file_name)
            try:
                os.rename(old_file_path, new_file_path)
                QMessageBox.information(self, "File Renamed", f"Renamed file to {new_file_name}")
                self.go_back()  # Go back to the previous window after renaming the file
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename file: {e}")

    def delete_maya_file(self, file_name):
        file_path = os.path.join(self.project_assets_path, file_name)
        reply = QMessageBox.question(self, 'Delete Maya File', f"Are you sure you want to delete the file '{file_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                QMessageBox.information(self, "File Deleted", f"Deleted file '{file_name}'")
                self.go_back()  # Go back to the previous window after successful deletion
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")

    def go_back(self):
        if self.previous_window:
            self.previous_window.show()
        self.close()

    def create_maya_file(self):
        file_name, ok = QInputDialog.getText(self, 'Create Maya File', 'Enter Maya file name:')
        if ok and file_name:
            file_path = os.path.join(self.project_assets_path, file_name + '.ma')
            try:
                with open(file_path, 'w') as file:
                    file.write("//Maya ASCII 2024 scene\n")  # Header for a basic Maya ASCII file
                QMessageBox.information(self, "File Creation", f"Created Maya file: {file_name}")
                self.open_maya_file_and_exit(file_path)  # Open the new Maya file and exit the application
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create Maya file: {e}")

    def open_maya_file_and_exit(self, file_path):
        maya_executable = "C:/Program Files/Autodesk/Maya2024/bin/maya.exe"
        try:
            subprocess.Popen([maya_executable, file_path])
            QApplication.instance().quit()  # Exit the application after launching Maya
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Maya file: {e}")

    def copy_maya_file(self, file_name):
        # Hardcoded path to the Maya files
        source_file_path = os.path.join("C:/Autodesk/Autodesk_Maya_2024_1_Update_Windows_64bit_dlm/Company name/PMT Projects/Project Assets", file_name)
        self.project_selection_window = ProjectSelectionWindow(os.path.join("C:/Autodesk/Autodesk_Maya_2024_1_Update_Windows_64bit_dlm/Company name", "PMT Projects"),
                                                               copy_source_path=source_file_path,
                                                               previous_window=self)
        self.project_selection_window.show()
        self.close()

class MayaFileOptionsWindow(QWidget, CenteredWindowMixin):
    def __init__(self, project_path, previous_window=None):
        super().__init__()
        self.setWindowTitle('Maya File Options')
        self.setGeometry(150, 150, 400, 200)
        self.project_path = project_path
        self.previous_window = previous_window  # Reference to the previous window
        self.initUI()
        self.center_window()

    def initUI(self):
        layout = QVBoxLayout()

        # Buttons for various Maya file options
        create_button = QPushButton('Create New Maya File')
        create_button.clicked.connect(self.create_new_maya_file)
        layout.addWidget(create_button)

        edit_button = QPushButton('Edit Existing Maya File')
        edit_button.clicked.connect(self.edit_existing_maya_file)
        layout.addWidget(edit_button)

        delete_button = QPushButton('Delete Maya File')
        delete_button.clicked.connect(self.delete_maya_file)
        layout.addWidget(delete_button)

        rename_button = QPushButton('Rename Maya File')  # New button for renaming
        rename_button.clicked.connect(self.rename_maya_file)  # Connect to the handler method
        layout.addWidget(rename_button)

        copy_button = QPushButton('Copy Maya File')
        copy_button.clicked.connect(self.copy_maya_file)
        layout.addWidget(copy_button)

        back_button = QPushButton('Back')
        back_button.setFixedSize(60, 30)  # Set smaller size for the Back button
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def create_new_maya_file(self):
        self.folder_selection_window = FolderSelectionWindow(self.project_path, new_file=True, previous_window=self)
        self.folder_selection_window.show()
        self.close()  # Close the current window

    def edit_existing_maya_file(self):
        self.folder_selection_window = FolderSelectionWindow(self.project_path, new_file=False, previous_window=self)
        self.folder_selection_window.show()
        self.close()  # Close the current window

    def delete_maya_file(self):
        self.folder_selection_window = FolderSelectionWindow(self.project_path, delete_file=True, previous_window=self)
        self.folder_selection_window.show()
        self.close()  # Close the current window

    def rename_maya_file(self):
        self.folder_selection_window = FolderSelectionWindow(self.project_path, rename_file=True, previous_window=self)
        self.folder_selection_window.show()
        self.close()  # Close the current window

    def copy_maya_file(self):
        self.source_file_selection_window = SourceFileSelectionWindow(self.project_path, previous_window=self)
        self.source_file_selection_window.show()
        self.close()  # Close the current window

    def go_back(self):
        self.previous_window.show()
        self.close()

class FolderSelectionWindow(QWidget, CenteredWindowMixin):
    def __init__(self, project_path, new_file=False, delete_file=False, rename_file=False, previous_window=None):
        super().__init__()
        self.setWindowTitle('Select Folder')
        self.setGeometry(200, 200, 400, 200)
        self.project_path = project_path
        self.new_file = new_file
        self.delete_file = delete_file
        self.rename_file = rename_file  # Add rename_file parameter
        self.previous_window = previous_window  # Reference to the previous window
        self.initUI()
        self.center_window()

    def initUI(self):
        layout = QVBoxLayout()
        source_folder = os.path.join(self.project_path, 'Source')
        subfolders = [f for f in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, f))]

        for folder in subfolders:
            button = QPushButton(folder)
            button.clicked.connect(self.folder_button_clicked)
            layout.addWidget(button)

        back_button = QPushButton('Back')
        back_button.setFixedSize(60, 30)  # Set smaller size for the Back button
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    # Function to handle button click for selecting a folder
    def folder_button_clicked(self):
        sender = self.sender()
        subfolder_path = os.path.join(self.project_path, 'Source', sender.text())
        if self.rename_file:  # If the user selected "Rename Maya File" option
            # Open the MayaFileSelectionWindow directly for renaming Maya files
            self.maya_file_selection_window = MayaFileSelectionWindow(subfolder_path, rename_file=True, previous_window=self.previous_window)
            self.maya_file_selection_window.show()
            self.close()  # Close the current window
        else:  # Default behavior for other options
            if self.new_file:
                try:
                    file_name, ok = QInputDialog.getText(self, 'Maya File Name', 'Enter Maya file name:')
                    if ok and file_name:
                        file_path = os.path.join(subfolder_path, file_name + '.ma')
                        with open(file_path, 'w') as file:
                            file.write("//Maya ASCII 2023 scene\n")  # Header for a basic Maya ASCII file
                        QMessageBox.information(self, "File Creation", f"Created Maya file!")
                        self.open_maya_file_and_exit(file_path)  # Open the new Maya file and exit the application
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to create Maya file: {e}")
            elif self.delete_file:
                self.maya_file_selection_window = MayaFileSelectionWindow(subfolder_path, delete_file=True, previous_window=self)
                self.maya_file_selection_window.delete_file_button_clicked.connect(self.handle_delete_file)
                self.maya_file_selection_window.show()
                self.close()  # Close the current window
            else:
                self.maya_file_selection_window = MayaFileSelectionWindow(subfolder_path, previous_window=self)
                self.maya_file_selection_window.show()
                self.close()  # Close the current window

    def handle_delete_file(self, file_path):
        try:
            os.remove(file_path)
            QMessageBox.information(self, "File Deletion", f"Deleted Maya file!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete Maya file: {e}")
        #self.go_back()  # Go back to the previous window after deletion
        self.close()

    def go_back(self):
        self.previous_window.show()
        self.close()

    def open_maya_file_and_exit(self, file_path):
        # Replace this path with the actual path to your Maya executable
        maya_executable = "C:/Program Files/Autodesk/Maya2024/bin/maya.exe"
        try:
            subprocess.Popen([maya_executable, file_path])
            QApplication.instance().quit()  # Exit the application after launching Maya
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Maya file: {e}")

# Define a window for selecting a source Maya file
class SourceFileSelectionWindow(QWidget, CenteredWindowMixin):
    def __init__(self, project_path, previous_window=None):
        super().__init__()
        self.setWindowTitle('Select Copy')
        self.setGeometry(300, 300, 400, 200)
        self.project_path = project_path
        self.previous_window = previous_window  # Reference to the previous window
        self.initUI()
        self.center_window()

    def initUI(self):
        layout = QVBoxLayout()
        subfolders = ['Source/Characters', 'Source/Environments', 'Source/Props']

        for folder in subfolders:
            button = QPushButton(folder.split('/')[-1])
            button.clicked.connect(self.folder_button_clicked)
            layout.addWidget(button)

        back_button = QPushButton('Back')
        back_button.setFixedSize(60, 30)  # Set smaller size for the Back button
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    # Function to handle button click for selecting a folder
    def folder_button_clicked(self):
        sender = self.sender()
        subfolder_path = os.path.join(self.project_path, 'Source', sender.text())
        self.maya_file_selection_window = MayaFileSelectionWindow(subfolder_path, copy_file=True, previous_window=self)
        self.maya_file_selection_window.show()
        self.close()  # Close the current window

    # Function to go back to the previous window
    def go_back(self):
        self.previous_window.show()
        self.close()

class MayaFileSelectionWindow(QWidget, CenteredWindowMixin):
    delete_file_button_clicked = pyqtSignal(str)

    def __init__(self, subfolder_path, delete_file=False, copy_file=False, rename_file=False, previous_window=None):
        super().__init__()
        self.setWindowTitle('Select Maya File')
        self.setGeometry(350, 350, 400, 200)
        self.subfolder_path = subfolder_path
        self.delete_file = delete_file
        self.copy_file = copy_file
        self.rename_file = rename_file
        self.previous_window = previous_window
        self.initUI()
        self.center_window()

    def initUI(self):
        layout = QVBoxLayout()
        maya_files = [f for f in os.listdir(self.subfolder_path) if f.endswith('.ma')]

        for file in maya_files:
            hbox = QHBoxLayout()

            file_button = QPushButton(file)
            file_button.clicked.connect(self.file_button_clicked)
            hbox.addWidget(file_button)

            layout.addLayout(hbox)

        back_button = QPushButton('Back')
        back_button.setFixedSize(60, 30)
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def file_button_clicked(self):
        sender = self.sender()
        maya_file_path = os.path.join(self.subfolder_path, sender.text())
        if self.delete_file:
            self.delete_file_button_clicked.emit(maya_file_path)
            self.go_back()
        elif self.copy_file:
            self.show_copy_options_dialog(maya_file_path)
        elif self.rename_file:
            self.rename_maya_file(maya_file_path)
        else:
            self.open_maya_file(maya_file_path)

    def show_copy_options_dialog(self, maya_file_path):
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Copy Options")
        message_box.setText("Where do you want to copy the Maya file?")
        project_button = message_box.addButton("Select Project", QMessageBox.AcceptRole)
        department_button = message_box.addButton("Department Assets", QMessageBox.AcceptRole)
        cancel_button = message_box.addButton(QMessageBox.Cancel)

        message_box.exec_()

        if message_box.clickedButton() == project_button:
            self.open_project_selection_window(maya_file_path)
        elif message_box.clickedButton() == department_button:
            self.copy_to_department_assets(maya_file_path)

    def copy_to_department_assets(self, maya_file_path):
        department_assets_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "Department Assets")
        if not os.path.exists(department_assets_path):
            QMessageBox.critical(self, "Error", "'Department Assets' folder does not exist!")
            return

        try:
            shutil.copy(maya_file_path, department_assets_path)
            QMessageBox.information(self, "File Copied", "Maya file copied to Department Assets folder successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy Maya file: {e}")

    def open_project_selection_window(self, maya_file_path):
        projects_path = os.path.join(BASE_DIRECTORY_PATH, COMPANY_NAME, "PMT Projects")
        if not os.path.exists(projects_path):
            QMessageBox.critical(self, "Error", f"'PMT Projects' folder does not exist!")
            return
        self.project_selection_window = ProjectSelectionWindow(projects_path, copy_source_path=maya_file_path, previous_window=self.previous_window)
        self.project_selection_window.show()
        self.close()

    def rename_maya_file(self, file_path):
        new_file_name, ok = QInputDialog.getText(self, 'Rename Maya File', 'Enter new Maya file name:', text=os.path.basename(file_path)[:-3])
        if ok and new_file_name:
            new_file_path = os.path.join(os.path.dirname(file_path), new_file_name + '.ma')
            try:
                os.rename(file_path, new_file_path)
                QMessageBox.information(self, "File Renamed", f"Renamed Maya file to {new_file_name}")
                self.go_back()  # Go back to the previous window after renaming the file
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename Maya file: {e}")

    def open_maya_file(self, file_path):
        # Print the file path for debugging
        print("File Path:", file_path)

        # Replace this path with the actual path to your Maya executable
        maya_executable = "C:/Program Files/Autodesk/Maya2024/bin/maya.exe"
        try:
            subprocess.Popen([maya_executable, file_path])
            sys.exit(0)  # Exit the application after opening the file
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Maya file: {e}")

    def go_back(self):
        self.previous_window.show()
        self.close()

if __name__ == "__main__":
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())