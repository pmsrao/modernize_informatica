# Phase 1 & Phase 2 Testing Guide

## Frontend Server Status
✅ Frontend server is running at: `http://localhost:5173`

## Testing URLs

### Modernization Journey (New Design)
- **URL**: `http://localhost:5173/#/modern/`
- This is the enhanced UI with sidebar navigation and modern design

### Simple View (Original)
- **URL**: `http://localhost:5173/#/simple/`
- Original UI for comparison

## Phase 1 Testing Checklist

### ✅ Layout & Navigation
1. **Sidebar Navigation**
   - [ ] Dark blue sidebar (#1E3A5F) is visible on the left
   - [ ] Application title "INFORMATICA MODERNIZATION ACCELERATOR" is displayed
   - [ ] Navigation menu items are visible:
     - Upload Files
     - Repository
     - Parse & AI Enhance
     - Canonical Model
     - Lineage
     - Generate Code
   - [ ] Active step is highlighted in light blue (#4A90E2)
   - [ ] Clicking menu items navigates to the correct step
   - [ ] Step counter shows "Step X of 6" at the bottom

2. **Top Header**
   - [ ] Light blue header (#E3F2FD) is visible at the top
   - [ ] "BiCXO" logo/brand name is displayed
   - [ ] Tenant selector dropdown shows "apple.inc"
   - [ ] Upload icon is visible
   - [ ] Notification bell icon is visible
   - [ ] Profile avatar is visible

3. **Progress Indicator**
   - [ ] Progress bar shows "Step X of 6: [Step Name]"
   - [ ] Step description is displayed below the title
   - [ ] Progress bar fills based on current step
   - [ ] Progress percentage (X/6) is visible

### ✅ Step 1: Upload Files
1. **Drag & Drop Zone**
   - [ ] Large dashed border upload zone is visible
   - [ ] Cloud icon with up arrow is displayed
   - [ ] "Drag & Drop Files Here" text is visible
   - [ ] "or browse to upload XML files" instruction is shown
   - [ ] "Browse Files" button is present
   - [ ] Can drag and drop XML files
   - [ ] Can click "Browse Files" to select files
   - [ ] Can use "Select Folder to Upload" for directory upload

2. **Uploaded Files List**
   - [ ] After upload, files are listed with icons
   - [ ] File type badges are displayed (MAPPING, WORKFLOW, etc.)
   - [ ] "Next: Repository View →" button appears
   - [ ] Clicking next navigates to Step 2

## Phase 2 Testing Checklist

### ✅ Step 3: Parse & Enhance Complete
1. **Success Message**
   - [ ] Green checkmark icon is displayed
   - [ ] "Parse & Enhance Complete!" message is shown
   - [ ] Description text explains what was done
   - [ ] Card has gradient background (green to white)

2. **Mapping List**
   - [ ] "Available Mappings (X)" section is visible
   - [ ] Mappings are displayed as blue chips/pills
   - [ ] Can click on a mapping chip to view canonical model
   - [ ] "Back to Repository" button works
   - [ ] "View Canonical Model →" button works

### ✅ Step 4: Canonical Model View
1. **Mapping Selector**
   - [ ] Mapping name is displayed with navigation arrows
   - [ ] Can navigate to previous mapping (if available)
   - [ ] Can navigate to next mapping (if available)
   - [ ] Current position (X of Y) is shown
   - [ ] "Back to Repository" button works

2. **Statistics Panel**
   - [ ] Three statistics cards are displayed:
     - Total Mappings (blue card)
     - Total Transformations (orange card)
     - Total Tables (green card)
   - [ ] Numbers are displayed prominently
   - [ ] Labels are clear and readable

3. **Graph Explorer**
   - [ ] Graph visualization is displayed
   - [ ] Nodes and edges are visible
   - [ ] Can interact with the graph (zoom, pan)
   - [ ] Graph is properly contained in the card

4. **Action Buttons**
   - [ ] "View Lineage" button is visible
   - [ ] "Generate Code" button is visible
   - [ ] Both buttons have icons
   - [ ] Buttons are properly styled

### ✅ Step 6: Generate Code
1. **Tab Navigation**
   - [ ] Three tabs are visible: PySpark | DLT | SQL
   - [ ] Active tab is highlighted
   - [ ] Can switch between tabs
   - [ ] Tab colors match design (blue, purple, green)

2. **Code Generation**
   - [ ] Clicking a tab generates code for that type
   - [ ] Loading state is shown while generating
   - [ ] Code appears after generation

3. **Code Viewer**
   - [ ] Code is displayed with syntax highlighting
   - [ ] Dark theme code viewer is used
   - [ ] Copy button is visible in the header
   - [ ] Can copy code to clipboard
   - [ ] Copy confirmation (checkmark) appears
   - [ ] File name is displayed in the header
   - [ ] Code is scrollable if long

4. **Action Button**
   - [ ] "Enhance/Fix with AI" button is visible
   - [ ] Button navigates to Step 7

### ✅ Step 7: AI Enhance
1. **Review Section**
   - [ ] "AI Code Review & Enhancement" title is visible
   - [ ] Description explains what AI will do
   - [ ] "Review Code with AI" button is present
   - [ ] Button is disabled if no code is generated

2. **Review Results**
   - [ ] After review, results are displayed
   - [ ] Issues are shown with severity indicators:
     - HIGH issues: Red with error icon
     - MEDIUM issues: Orange with warning icon
     - LOW issues: Purple with info icon
   - [ ] Each issue shows:
     - Category/Type
     - Severity badge
     - Description/Message
     - Location (if available)
     - Recommendation (if available)
   - [ ] Recommendations have lightbulb icon
   - [ ] "Clear" button resets the results

3. **Success State**
   - [ ] If no issues found, success message is displayed
   - [ ] Green checkmark icon is shown
   - [ ] "No issues found! Code looks good." message

## Common Issues to Check

### Visual Issues
- [ ] No layout breaks on different screen sizes
- [ ] Colors match the design screenshots
- [ ] Icons are properly displayed
- [ ] Text is readable and properly sized
- [ ] Spacing is consistent throughout

### Functional Issues
- [ ] All navigation works correctly
- [ ] File upload works (both drag-drop and folder)
- [ ] Parse & enhance works
- [ ] Code generation works for all types (PySpark, DLT, SQL)
- [ ] AI review works
- [ ] All buttons trigger correct actions
- [ ] No console errors

### Performance
- [ ] Page loads quickly
- [ ] No lag when switching between steps
- [ ] Graph visualization is smooth
- [ ] Code viewer doesn't freeze with large code

## Testing Workflow

### Complete End-to-End Test
1. Navigate to `http://localhost:5173/#/modern/`
2. **Step 1**: Upload XML files (use `samples/super_complex/*.xml`)
3. **Step 2**: View repository, verify files are listed
4. **Step 3**: Parse mappings (use "Parse All Mappings" button)
5. **Step 4**: View canonical model, check statistics, navigate mappings
6. **Step 5**: View lineage (if workflow files uploaded)
7. **Step 6**: Generate code for each type (PySpark, DLT, SQL)
8. **Step 7**: Review code with AI, check issue display

## Known Issues / Notes

- The sidebar is fixed at 240px width
- The header accounts for the sidebar width
- Progress indicator shows step title and description
- All functionality from the original UI is preserved

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)

## Next Steps After Testing

If you find any issues:
1. Note the step where the issue occurs
2. Describe what you expected vs. what happened
3. Check browser console for errors
4. Share screenshots if possible

If everything works:
- Phase 1 & 2 are complete! ✅
- Ready to proceed with additional enhancements or Phase 3

