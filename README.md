# EMAV - Experimental Modal Analysis Viewer (v0.4.0)

## Description

EMAV (Experimental Modal Analysis Viewer) is a bespoke software tool developed in Python, designed for the visualization, comparative analysis, and **quantitative validation** of experimental modal analysis data. Version 0.4.0 introduces a **dual-tree interface** for efficient management of multiple reconstructed signals alongside testlab data.

The tool supports both multi-record `.unv` and `.mat` files from testing software and single-record, linear-amplitude `.unv` files representing reconstructed signals.

---

## Key Features

### **NEW in v0.4.0: Enhanced Interface**

#### **Dual-Tree View**
- **Left Tree**: Testlab signals from one comprehensive file
- **Right Tree**: Multiple reconstructed signal files
- **Independent Selection**: Choose one signal from each tree for comparison
- **Visual Organization**: Clear separation of reference and reconstructed data

#### **Multiple Reconstructed File Support**
- Load multiple reconstructed `.unv` files simultaneously
- Each file displayed as a separate node in the reconstructed tree
- Quick switching between different reconstructed signals
- Batch file loading with success/failure reporting

#### **Phase Display Toggle**
- **"Show Phase" checkbox** to hide/show the phase subplot
- Save screen space when phase information not needed
- Maintains all data - only affects visualization
- Works seamlessly with logarithmic/linear scale toggle

### Core Functionality
- **Dual Data Source Loading**: Load multi-record Testlab files (`.unv`, `.mat`) and multiple reconstructed FRF files (`.unv`).
- **Interactive Tree Views**: Navigate through different records with dedicated trees for testlab and reconstructed signals.
- **Dual-Plot Comparison**:
    - Top plot: Selected reconstructed signal (linear scale)
    - Bottom plot: Selected testlab record (magnitude + optional phase)
- **Dynamic Scale Control**:
    - Toggle testlab amplitude plot between **logarithmic** and **linear** scales
    - **Show/Hide phase plot** for cleaner display
    - Manually adjust X/Y axis limits on reconstructed plot
- **Smart Data Handling**: Automatically distinguishes between complex-valued FRF data and real-valued data
- **Data Export**: Save selected testlab records as linear-amplitude `.unv` files

### Quantitative Validation Metrics

EMAV includes a comprehensive validation framework based on the *Scientific Validation Guide for Reconstructed Frequency Response Functions* (October 2025):

#### **1. Global Error Metrics**
- **RMSE (Root Mean Squared Error)**: Average error magnitude
- **MAE (Mean Absolute Error)**: Average absolute deviation
- **R² (Coefficient of Determination)**: Linear correlation measure

#### **2. Advanced Shape Metrics**
- **FRAC (Frequency Response Assurance Criterion)**: Industry-standard shape consistency metric (0-1 scale)

#### **3. Feature-Specific Peak Analysis**
- **Automated Peak Detection**: Prominence-based algorithm
- **Peak Matching**: Automatic pairing with 5% frequency tolerance
- **Detailed Comparison**: Frequency and magnitude errors for each peak

---

## Current Status (v0.4.0)

**Status**: Production Release

**What's New in v0.4.0**:
- ✅ Dual-tree interface (Testlab | Reconstructed)
- ✅ Multiple reconstructed file loading
- ✅ Phase display toggle (Show/Hide)
- ✅ Enhanced file management ("Clear Reconstructed" button)
- ✅ Improved selection workflow
- ✅ Better visual organization

**Previous Features (v0.3.0)**:
- ✅ Custom UNV parser for simplified formats
- ✅ Comprehensive validation metrics (RMSE, R², FRAC, Peak Analysis)
- ✅ All original visualization features

---

## Installation and Setup

EMAV is designed to be run from a local folder without complex installation.

**Prerequisites**:
- Python 3.12 or newer

**Instructions**:
1. Place the following files into a single folder:
   - `emav_app.py` (v0.4.0)
   - `requirements.txt`
   - `RUN_EMAV.bat`
2. Add your `.unv` and `.mat` data files to the same folder
3. Double-click `RUN_EMAV.bat`

The batch file will:
- Create a Python virtual environment (`emavenv`)
- Install all dependencies
- Launch the EMAV application

---

## Usage Guide

### Basic Workflow

#### **1. Load Testlab Data**
- Click **"Load Testlab File"**
- Select your `.unv` or `.mat` file containing all test signals
- Records appear in the **left tree view**

#### **2. Load Reconstructed Signals**
- Click **"Load Reconstructed Files"**
- Select one or more `.unv` files (Ctrl+Click for multiple selection)
- Files appear in the **right tree view**
- Each file can be expanded to show its records

#### **3. Select Signals for Comparison**
- Click on a **testlab record** in the left tree (bottom plot updates)
- Click on a **reconstructed record** in the right tree (top plot updates)
- Both selections remain active until changed

#### **4. Customize Display**
- **Show Phase**: Toggle phase subplot visibility
- **Log Scale**: Switch between logarithmic and linear Y-axis
- **X/Y Limits**: Manually adjust reconstructed plot zoom
- **Reset Scale**: Return to auto-scale view

#### **5. Validate Quality**
- Ensure both testlab and reconstructed signals are selected
- Click **"Calculate Validation Metrics"**
- Review comprehensive report in metrics panel

### Advanced Features

#### **Multiple File Comparison**
1. Load multiple reconstructed files
2. Select different files from the right tree to compare
3. Validation metrics update for each new selection
4. No need to reload files

#### **Clear and Reload**
- **"Clear Reconstructed"** button removes all reconstructed files
- Testlab data remains loaded
- Useful for starting fresh comparisons

#### **Save Testlab Records**
- Select a testlab record (left tree)
- Click **"Save Selected Testlab Record"**
- Exports as linear-amplitude `.unv` file
- Compatible format for reconstructed signals

---

## Interface Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  [Load Testlab] [Load Reconstructed Files] [Clear Reconstructed] │
├──────────────┬──────────────┬────────────────────────────────────┤
│  Testlab     │ Reconstructed│                                    │
│  Signals     │ Signals      │     Reconstructed FRF Plot         │
│              │              │     (Selected from Right Tree)     │
│  ├─File.unv  │ ├─File1.unv  │                                    │
│  │ ├─Rec 1   │ │ └─Record 1 │     [X/Y Min/Max] [Apply] [Reset] │
│  │ ├─Rec 2   │ ├─File2.unv  │                                    │
│  │ └─Rec 3   │ │ └─Record 1 ├────────────────────────────────────┤
│              │ └─File3.unv  │     Testlab FRF Plot               │
│ (Select One) │   └─Record 1 │     (Selected from Left Tree)      │
│              │ (Select One) │     - Magnitude (always shown)     │
│              │              │     - Phase (optional)             │
│              │              │                                    │
│              │              │  [☑ Show Phase] [☑ Log Scale]     │
│              │              │  [Save Selected Testlab Record]    │
│              │              ├────────────────────────────────────┤
│              │              │  Validation Metrics Report         │
│              │              │  [Calculate Validation Metrics]    │
└──────────────┴──────────────┴────────────────────────────────────┘
```

---

## Quantitative Validation Workflow

### Prerequisites
- One testlab record selected (left tree)
- One reconstructed record selected (right tree)

### Steps
1. Select your signals in both trees
2. Click **"Calculate Validation Metrics"**
3. Review the comprehensive report:

```
===============================================================
            QUANTITATIVE VALIDATION METRICS REPORT
===============================================================

[1] GLOBAL ERROR METRICS
    RMSE: X.XXXXe-XX
    MAE:  X.XXXXe-XX
    R²:   0.XXXXXX → Quality assessment

[2] ADVANCED SHAPE METRICS
    FRAC: 0.XXXXXX → Shape consistency rating

[3] FEATURE-SPECIFIC ANALYSIS: RESONANT PEAKS
    Peaks detected: X original, Y reconstructed, Z matched
    
    Peak #1:
      Frequency Error: ±X.XX Hz (±X.XX%)
      Magnitude Error: ±X.XXe-XX (±X.XX%)
    ...
```

### Interpretation Guidelines

**FRAC (Shape Similarity):**
- **> 0.95**: Excellent reconstruction
- **0.85-0.95**: Good reconstruction
- **0.70-0.85**: Moderate reconstruction
- **< 0.70**: Poor reconstruction (review method)

**R² (Linear Correlation):**
- **> 0.95**: Excellent correlation
- **0.85-0.95**: Good correlation
- **0.70-0.85**: Moderate correlation
- **< 0.70**: Poor correlation

---

## Dependencies

The following Python packages are required (automatically installed via `requirements.txt`):

- `tkinter` (Standard with Python)
- `scipy` - Signal processing and peak detection
- `numpy` - Numerical operations
- `matplotlib` - Plotting
- `pyuff` - UNV file I/O
- `scikit-learn` - R² calculation

### requirements.txt
```txt
scipy
numpy
matplotlib
pyuff
scikit-learn
```

---

## Mathematical Background

### RMSE (Root Mean Squared Error)
```
RMSE = sqrt(1/N * Σ(|y_i| - |ŷ_i|)²)
```

### R² (Coefficient of Determination)
```
R² = 1 - Σ(|y_i| - |ŷ_i|)² / Σ(|y_i| - |ȳ|)²
```

### FRAC (Frequency Response Assurance Criterion)
```
FRAC = |{Y_A}^H {Y_B}|² / ({Y_A}^H {Y_A})({Y_B}^H {Y_B})
```
Uses Hermitian (conjugate) transpose via `np.vdot()`

### Peak Analysis
- Detection: `scipy.signal.find_peaks` with 10% prominence threshold
- Matching: Nearest-neighbor with 5% frequency tolerance

---

## Known Limitations

1. **Phase Information**: Reconstructed FRFs assumed to have zero phase (amplitude only)
2. **Complex Data Requirement**: Validation requires complex FRF data (not PSD/Coherence)
3. **Peak Matching**: Simple nearest-neighbor algorithm (may need refinement for dense modal spacing)
4. **Export from .mat**: Saving transformed records only supported for `.unv` files

---

## Troubleshooting

### "Failed to load Reconstructed FRF file"
- Ensure file is valid `.unv` with Dataset 58
- Check console output for detailed error messages
- Verify file contains amplitude data

### "Validation requires complex data"
- Ensure testlab record is FRF (complex), not PSD or Coherence (real)
- Select a different record from the testlab tree

### No peaks detected
- Prominence threshold may be too high (10% of max amplitude)
- Select a record with more prominent resonances
- Verify peaks are visible in the plots

### FRAC calculation fails
- Zero-energy signal detected
- Verify both signals contain non-zero data

### Multiple files not loading
- Check console for per-file error messages
- Some files may load while others fail
- Status bar shows success/failure count

---

## Version History

### v0.4.0 (Current Release)
- ✅ Dual-tree interface (Testlab | Reconstructed)
- ✅ Multiple reconstructed file loading
- ✅ Phase display toggle (Show/Hide checkbox)
- ✅ Clear reconstructed files button
- ✅ Enhanced selection workflow
- ✅ Improved visual organization
- ✅ Better space utilization

### v0.3.0
- ✅ Custom UNV parser for simplified Dataset 58 format
- ✅ Comprehensive validation metrics (RMSE, MAE, R², FRAC)
- ✅ Automated peak detection and comparison
- ✅ Validation metrics panel with interpretation guidelines
- ✅ Enhanced GUI layout

### v0.2.1
- ✅ Fixed `.unv` file loading with temporary file workaround
- ✅ Stable testlab file loading and plotting
- ✅ Core visualization features

### v0.2.0
- Initial release with basic comparison features

---

## Keyboard Shortcuts

- **Tree Navigation**: Arrow keys to move between records
- **Tree Expansion**: Enter to expand/collapse nodes
- **Multi-Select Files**: Ctrl+Click in file dialog for multiple reconstructed files

---

## Tips for Efficient Workflow

1. **Load Once, Compare Many**: Load all your reconstructed files at the start, then quickly switch between them
2. **Use Phase Toggle**: Hide phase when not needed for cleaner display and better amplitude focus
3. **Name Files Clearly**: Reconstructed filenames appear in the tree - descriptive names help organization
4. **Batch Validation**: With multiple files loaded, systematically validate each against the same testlab record
5. **Save Validated Matches**: Use "Save Selected Testlab Record" to export confirmed matches

---

## References

The validation methodology is based on:

1. **Allemang, R. J., & Brown, D. L. (1982).** "A correlation coefficient for modal vector analysis." *Proceedings of the 1st International Modal Analysis Conference (IMAC)*, 1, 110-116.

2. **Ewins, D. J. (2000).** *Modal Testing: Theory, Practice and Application* (2nd ed.). Research Studies Press.

3. **Pascual, R., Golinval, J. C., & Razeto, M. (1997).** "A frequency domain correlation technique for the comparison of models." *Proceedings of the 15th International Modal Analysis Conference (IMAC)*.

---

## Support

For issues or questions, refer to console output for detailed error messages. The application includes extensive logging to aid troubleshooting.

---

## License

This is a bespoke tool developed for internal use. Please consult with your organization regarding distribution and licensing terms.

---

**EMAV v0.4.0** - Enhanced interface for efficient multi-signal validation.