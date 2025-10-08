# Lab Instrument Manager - Module Dependencies

## 📊 Module Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    main.py                                     │
│                              (Application Entry Point)                         │
└─────────────────────┬───────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                main_window.py                                  │
│                              (CentralWindow - Main UI Controller)              │
└─────┬───────────────┬───────────────┬───────────────┬───────────────┬───────────┘
      │               │               │               │               │
      ▼               ▼               ▼               ▼               ▼
┌──────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│database.py│  │login_window.py│  │main_menu.py│  │date_utils.py│  │src/ui/windows/│
│(Database) │  │(LoginWindow) │  │(MainMenu)  │  │(Date Utils) │  │(UI Windows) │
└──────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
      │               │               │               │               │
      │               │               │               │               ▼
      │               │               │               │      ┌─────────────────┐
      │               │               │               │      │instruments_window│
      │               │               │               │      │maintenance_window│
      │               │               │               │      │users_window     │
      │               │               │               │      └─────────────────┘
      │               │               │               │               │
      │               │               │               │               ▼
      │               │               │               │      ┌─────────────────┐
      │               │               │               │      │src/ui/dialogs/  │
      │               │               │               │      │(Dialog Windows) │
      │               │               │               │      └─────────────────┘
      │               │               │               │               │
      │               │               │               │               ▼
      │               │               │               │      ┌─────────────────┐
      │               │               │               │      │add_instrument_  │
      │               │               │               │      │add_maintenance_ │
      │               │               │               │      │add_user_        │
      │               │               │               │      │instrument_details│
      │               │               │               │      │user_details     │
      │               │               │               │      └─────────────────┘
      │               │               │               │
      │               │               │               ▼
      │               │               │      ┌─────────────────┐
      │               │               │      │src/reports/     │
      │               │               │      │(PDF Generation) │
      │               │               │      └─────────────────┘
      │               │               │               │
      │               │               │               ▼
      │               │               │      ┌─────────────────┐
      │               │               │      │maintenance_report│
      │               │               │      │file_dialog      │
      │               │               │      └─────────────────┘
      │               │               │
      │               │               ▼
      │               │      ┌─────────────────┐
      │               │      │src/ui/base/     │
      │               │      │(Base Classes)   │
      │               │      └─────────────────┘
      │               │               │
      │               │               ▼
      │               │      ┌─────────────────┐
      │               │      │base_data_window │
      │               │      │base_dialog      │
      │               │      │base_table       │
      │               │      └─────────────────┘
      │               │
      │               ▼
      │      ┌─────────────────┐
      │      │src/utils/       │
      │      │(Utility Functions)│
      │      └─────────────────┘
      │               │
      │               ▼
      │      ┌─────────────────┐
      │      │path_utils.py    │
      │      │(Path Management)│
      │      └─────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              External Dependencies                             │
└─────────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PyQt6 (GUI Framework)  │  sqlite3 (Database)  │  bcrypt (Password Hashing)   │
│  reportlab (PDF)        │  datetime (Dates)    │  os, sys, signal (System)   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔍 Detailed Module Descriptions

### Core Application Modules
- **`main.py`** - Application entry point, creates QApplication and shows main window
- **`main_window.py`** - Central window controller, manages all UI components and database
- **`database.py`** - Database connection and operations (SQLite3)
- **`login_window.py`** - User authentication interface
- **`main_menu.py`** - Main navigation menu
- **`date_utils.py`** - Date calculation and formatting utilities

### UI Windows (`src/ui/windows/`)
- **`instruments_window.py`** - Instrument management interface
- **`maintenance_window.py`** - Maintenance records interface  
- **`users_window.py`** - User management interface

### UI Dialogs (`src/ui/dialogs/`)
- **`add_instrument_dialog.py`** - Add new instrument dialog
- **`add_maintenance_dialog.py`** - Add maintenance record dialog
- **`add_user_dialog.py`** - Add new user dialog
- **`instrument_details_dialog.py`** - Instrument details and history
- **`user_details_dialog.py`** - User details and management

### Base Classes (`src/ui/base/`)
- **`base_data_window.py`** - Base class for data management windows (instruments, maintenance, users)
- **`base_dialog.py`** - Base class for dialog windows with common functionality
- **`base_table.py`** - Base class for table widgets with sorting and highlighting

### Reports (`src/reports/`)
- **`maintenance_report.py`** - PDF report generation for maintenance records
- **`file_dialog.py`** - File save dialog for PDF reports

### Utilities (`src/utils/`)
- **`path_utils.py`** - Path management utilities for executable and database paths

### Build and Setup
- **`build.py`** - PyInstaller build script
- **`create_database.py`** - Database initialization script
- **`requirements.txt`** - Python dependencies
- **`main.spec`** - PyInstaller specification file

## 🔄 Data Flow

1. **Application Start**: `main.py` → `main_window.py`
2. **Authentication**: `main_window.py` → `login_window.py` → `database.py`
3. **Navigation**: `main_window.py` → `main_menu.py` → UI Windows
4. **Data Operations**: UI Windows → `database.py` (with WAL mode for concurrent access)
5. **Reports**: UI Windows → `src/reports/` → PDF Generation
6. **Utilities**: All modules → `date_utils.py`, `path_utils.py`
7. **Profile Management**: `main_menu.py` → `user_details_dialog.py` (self-service editing)

## 🏗️ Architecture Patterns

- **MVC Pattern**: UI (Views) ↔ Database (Model) ↔ Controllers (Windows)
- **Inheritance**: Base classes provide common functionality
- **Dependency Injection**: Database instance passed to child components
- **Signal/Slot**: PyQt6 signals for component communication
- **WAL Mode**: SQLite Write-Ahead Logging for concurrent database access
- **State Management**: Dialog state tracking to prevent multiple instances

## 🚀 Current Features & Improvements

### Database & Concurrency
- **WAL Mode**: Multiple users can access the application simultaneously
- **Connection Timeout**: 30-second timeout for database operations
- **No File Locking**: Removed file-based locking system for better performance

### User Interface
- **Self-Service Profile Editing**: Users can edit their own profiles
- **Enhanced Permissions**: Admin-only buttons visible but locked for normal users
- **Optimized Table Display**: Last columns size to content instead of stretching
- **Consistent Delete Validation**: Unified selection validation across all tables

### User Management
- **Dropdown User Types**: Replaced checkboxes with user type dropdowns
- **Password Complexity**: Enhanced password validation with uppercase requirements
- **Performed By Selection**: Maintenance records can specify responsible person

### Maintenance Operations
- **Primary Key Deletion**: Fixed double-row deletion issue using record IDs
- **Enhanced Maintenance Dialog**: Better user selection and validation
- **PDF Report Generation**: Automatic PDF generation for maintenance records
