# Releases

This folder contains stable releases of the Lab Instrument Manager application.

## Release Structure
```
releases/
├── README.md              # This file
├── v1.0.0/               # Version 1.0.0 release
│   ├── main.exe          # Application executable
│   ├── lab_instruments.db # Database file
│   └── README.md         # Release-specific documentation
└── [future versions...]
```

## Release Process

### Creating a New Release
1. **Build the Application:**
   ```bash
   python build.py
   ```

2. **Test the Build:**
   - Run the executable from `dist/` folder
   - Verify all features work correctly
   - Test with sample data

3. **Create Release Folder:**
   ```bash
   mkdir releases/v[version]
   ```

4. **Copy Release Files:**
   ```bash
   copy dist\main.exe releases\v[version]\
   copy dist\lab_instruments.db releases\v[version]\
   ```

5. **Update Documentation:**
   - Update version number in release README
   - Document new features/changes
   - Update installation instructions if needed

6. **Commit and Tag:**
   ```bash
   git add releases/
   git commit -m "Release v[version]"
   git tag v[version]
   git push origin main --tags
   ```

## Versioning
- **Major.Minor.Patch** format (e.g., v1.0.0)
- **Major:** Breaking changes
- **Minor:** New features, backward compatible
- **Patch:** Bug fixes, backward compatible

## Distribution
- Each release folder is self-contained
- Users can download the entire folder
- No additional dependencies required
- Database included with sample data

## Current Releases
- **v1.0.0** (July 6, 2025) - Initial stable release
  - Instrument management
  - Maintenance tracking
  - User management
  - PDF reports
  - Professional UI 