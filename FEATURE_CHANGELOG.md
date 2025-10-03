# FTC Field Viewer v2.1.0 - Show/Hide Default Points Feature

## 🎉 New Feature Added!

Added a new checkbox in the control panel to **show or hide default points**, giving users more control over the display.

### ✨ **What's New:**

#### **1. Show/Hide Default Points Control**
- New checkbox: **"Show default points"** in the Grid section of the control panel
- Located right below the "Show point labels" checkbox
- Checked by default (maintains existing behavior)

#### **2. Enhanced Point Management**
- **Separated default points from user points** internally
- Default points are loaded from `Default Points/*.json` files
- User-added points are tracked separately
- Both types can be edited, saved, and loaded independently

#### **3. Visual Point Distinction**
- **📍 Default points** - shown with pin emoji in the points list
- **🔹 User points** - shown with diamond emoji in the points list
- Easy visual identification of point types

#### **4. Improved Save/Load System**
- **Enhanced JSON format** saves both default and user points separately
- **Backward compatibility** - old JSON files still load correctly (treated as user points)
- **Preserves settings** - remembers show/hide preference when saving/loading

### 🔧 **Technical Changes:**

#### **Core Implementation:**
- `self.default_points` - stores points from Default Points directory
- `self.user_points` - stores user-added points  
- `self.show_default_points` - controls visibility of default points
- `@property points` - dynamically combines visible points

#### **New Methods:**
- `set_show_default_points(show: bool)` - controls default point visibility
- Enhanced `save_points()` and `load_points()` with metadata support
- Updated point editing methods to work with the new structure

#### **UI Enhancements:**
- New checkbox in control panel
- Updated points list with visual indicators
- Automatic refresh when visibility changes

### 🎯 **User Benefits:**

1. **Cleaner View** - Hide default points when they're not needed
2. **Focus on Custom Work** - Show only user-added points during planning
3. **Better Organization** - Visual distinction between point types
4. **Flexible Workflow** - Toggle visibility as needed without losing data
5. **Backwards Compatible** - Existing point files continue to work

### 🚀 **Usage:**

1. **Toggle Default Points:**
   - Check/uncheck "Show default points" in the control panel
   - Default points appear/disappear immediately

2. **Visual Identification:**
   - 📍 **Default points** (from Default Points directory)
   - 🔹 **User points** (manually added)

3. **Save/Load:**
   - Save preserves both point types and visibility settings
   - Load maintains backwards compatibility with old files

### 📝 **Version History:**
- **v2.1.0** - Added show/hide default points feature
- **v2.0.0** - (Previous version with build system)
- **v1.0.0** - Initial release

The feature integrates seamlessly with the existing interface and maintains full compatibility with previous versions while adding powerful new functionality for managing point visibility.