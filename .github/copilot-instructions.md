# networthdash - Net Worth Dashboard

**ALWAYS follow these instructions first and only search for additional context if the information here is incomplete or found to be in error.**

networthdash is a Python package that generates personal finance dashboards from CSV data files using matplotlib and ausankey for visualization. The package creates comprehensive net worth visualizations including trends, projections, and breakdowns of assets, income, and expenditure.

## Working Effectively

### Environment Setup and Dependencies
**CRITICAL**: Set appropriate timeouts for all installation and build commands. Network connectivity issues are common.

- **Install Hatch (build system)**: `pipx install hatch` -- Takes 3-5 minutes. **NEVER CANCEL**: Set timeout to 10+ minutes.
- **Install dependencies**: `hatch run test:test` -- **NEVER CANCEL**: Takes 10-20 minutes on first run due to dependency downloads and environment creation. Set timeout to 30+ minutes.
- **Alternative dependency installation**: `pip install matplotlib ausankey numpy pandas pytest coverage mkdocs mkdocstrings[python]` -- **NEVER CANCEL**: Takes 15+ minutes. Set timeout to 25+ minutes.
- **If network issues occur**: Dependencies may fail to install due to PyPI connection timeouts. Document as "pip install -- fails due to network/firewall limitations" and try alternative approaches or retry with longer timeouts.

### Build and Test Commands
- **Run tests**: `hatch run test:test` -- **NEVER CANCEL**: Takes 5-15 seconds when dependencies are available (after first-time environment setup). Set timeout to 5+ minutes for safety.
- **Run tests with coverage**: `hatch run test:test-cov` -- **NEVER CANCEL**: Takes 10-20 seconds. Set timeout to 5+ minutes.
- **Format and lint code**: `hatch fmt` -- Takes 0.5-2 seconds. Always run before committing.
- **Check formatting only**: `hatch fmt --check` -- Takes 0.5-2 seconds. Returns exit code 1 if formatting issues found.
- **Note**: First run of any hatch command creates a new environment, adding 5-15 minutes to execution time. Subsequent runs are much faster.

### Documentation
- **Generate documentation**: `hatch run doc:ref` -- **NEVER CANCEL**: Takes 30-60 seconds. Set timeout to 5+ minutes.
- **Generate images**: `hatch run doc:img` -- **NEVER CANCEL**: Takes 30-90 seconds depending on data complexity. Set timeout to 10+ minutes.
- **Copy images**: `hatch run doc:icp` -- Takes 1-2 seconds.
- **Build documentation**: `mkdocs build` -- Takes 10-30 seconds. Set timeout to 5+ minutes.
- **Serve documentation locally**: `mkdocs serve` -- Starts development server on http://localhost:8000

### Application Usage
- **Run example dashboard**: `cd example && python nwd_example.py`
- **Basic usage pattern**:
  ```python
  import networthdash as nwd
  cfg = nwd.Config(
      csv = "your_data.csv",
      datefmt = "%Y-%m-%d",
      born_yr = 1981,
      retire_age = 67,
  )
  nwd.dashboard(cfg)
  ```

## Validation

### **MANUAL VALIDATION REQUIREMENT**
**CRITICAL**: Always test actual functionality by running complete user scenarios. Simply starting and stopping the application is NOT sufficient validation.

#### Essential Validation Scenarios
1. **Dashboard Generation Test**: 
   - Copy `example/nwd_example.csv` to working directory
   - Run dashboard generation with example data
   - Verify PNG/PDF output files are created
   - Check that the dashboard contains expected visualizations (net worth trends, income breakdown, shares analysis)

2. **Configuration Validation**:
   - Test with different date formats (`%Y-%m-%d`, `%Y/%m/%d`)
   - Test with missing data columns (use test files: `nwd_example_nocash.csv`, `nwd_example_noshares.csv`, etc.)
   - Verify error handling for malformed CSV files

3. **Output Format Testing**:
   - Test PDF generation: `cfg.savepdf = True`
   - Test PNG generation: `cfg.savepng = True`
   - Test anonymous mode: `cfg.anon = True`

### Pre-commit Validation
- **ALWAYS run**: `hatch fmt` to format code according to project standards
- **ALWAYS run**: `hatch run test:test` to ensure all tests pass
- **Check workflows will pass**: The CI build (`.github/workflows/`) will fail if formatting or tests fail

### Validated Test Data
The project includes 7 comprehensive test CSV files in `tests/` directory:
- `nwd_example.csv` - Full dataset (36 rows, 9 columns) with all data types
- `nwd_example_nocash.csv` - Missing cash data (36 rows, 7 columns)
- `nwd_example_noshares.csv` - Missing shares data (36 rows, 7 columns) 
- `nwd_example_nosuper.csv` - Missing superannuation data (36 rows, 7 columns)
- `nwd_example_noexpend.csv` - Missing expenditure data (36 rows, 7 columns)
- `nwd_example_noincome.csv` - Missing income data (36 rows, 5 columns)
- `nwd_example_nominor.csv` - Missing minor categories (36 rows, 7 columns)

Each test file represents a different real-world scenario of missing financial data.

### Common Test Scenarios
The test suite (`tests/test_nwd.py`) validates multiple data configurations:
- Full data (`nwd_example.csv`)
- Missing super data (`nwd_example_nosuper.csv`)
- Missing cash data (`nwd_example_nocash.csv`)
- Missing shares data (`nwd_example_noshares.csv`)
- Missing expenditure data (`nwd_example_noexpend.csv`)
- Missing income data (`nwd_example_noincome.csv`)
- Missing minor categories (`nwd_example_nominor.csv`)

Each test runs in both anonymous (`anon=True`) and normal (`anon=False`) modes.

## Project Structure

### Key Directories and Files
```
/
├── src/                    # Main source code
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Core dashboard generation logic
│   ├── config.py          # Configuration dataclass
│   ├── colors.py          # Color scheme definitions
│   └── strings.py         # String constants
├── tests/                 # Test suite and example data
│   ├── test_nwd.py        # Main test suite
│   └── nwd_example*.csv   # Test data files
├── docs/                  # Documentation source
│   ├── index.md           # Main documentation
│   ├── reference.md       # Code reference
│   ├── visualisation.md   # Visualization guide  
│   └── csv.md             # CSV format guide
├── example/               # Usage examples
│   ├── nwd_example.py     # Example usage script
│   └── nwd_example.csv    # Example data file
└── .github/
    └── workflows/         # CI/CD workflows
        ├── test.yml       # Test runner (pytest)
        ├── check.yml      # Linting (ruff)
        └── doc.yml        # Documentation build
```

### Hatch Environments
- **default**: Basic environment for development
- **test**: Testing environment with pytest, coverage, mkdocstrings
- **doc**: Documentation environment with mkdocs, mkdocstrings

### Core Dependencies
- **matplotlib**: Data visualization and plotting
- **ausankey**: Sankey diagram generation for flow visualization
- **numpy**: Numerical computations
- **pandas**: Data manipulation and CSV handling
- **pytest**: Testing framework
- **mkdocs**: Documentation generation

## Configuration and Customization

### Key Configuration Options (`src/config.py`)
- **CSV file settings**: `csv`, `csvdir`, `datefmt`
- **Personal settings**: `born_yr`, `retire_age`, `retire_ratio`
- **Output settings**: `savepdf`, `savepng`, `savejpg`, `savedir`
- **Visualization settings**: `figw`, `figh`, `colors`, `anon`
- **Analysis settings**: `linear_window`, `future_window`, `linear_targets`

### Color Scheme Customization (`src/colors.py`)
Default dark theme with customizable colors for:
- Background, axis, text, labels, titles
- Data series: super, total, shares, cash, expenditure
- Grid, dashes, frames, targets

### CSV Data Format
CSV files must have a specific two-row header structure:
- Row 1: Category (Shares, Cash, Super, Income, Expend)  
- Row 2: Subcategory (specific account names)
- Data rows: Date and corresponding values

Example structure:
```csv
,Shares,Shares,Cash,Super,Expend,Income,Income
Date,VAS,VGS,Daily,SuperSA,BuyShares,Pay,Dividend
2022-01-01,2750,2750,20000,100000,2750,8000,83
```

## Troubleshooting

### Network/Installation Issues
- **Dependency installation timeout**: Common with matplotlib and pandas. Typical error: "ReadTimeoutError: HTTPSConnectionPool(host='pypi.org', port=443): Read timed out." Use longer timeouts (20+ minutes) and retry.
- **PyPI connection issues**: May require retry or alternative index: `pip install --index-url https://pypi.org/simple/` or `pip install --timeout 300 --retries 3`
- **Build dependency failures**: Try `pip install --upgrade pip setuptools wheel` first, then retry main installation.
- **Hatch environment creation slow**: First-time environment creation downloads and installs all dependencies. Subsequent commands reuse the environment and are much faster.

### Runtime Issues
- **Import errors**: Ensure all dependencies are installed: `hatch run test:test` should pass without import failures
- **CSV parsing errors**: Verify CSV has correct two-row header structure (see example files in `tests/` directory)
- **Missing data handling**: Use test CSV files (`nwd_example_nocash.csv`, etc.) to validate behavior with missing columns
- **Display issues**: Dashboard generates matplotlib figures; ensure display environment supports graphics output

### Code Quality Issues
- **Linting failures**: `hatch fmt --check` identifies formatting issues. Current project has ~30 style issues that should be fixed.
- **Common linting issues found**: Blank lines with whitespace (W293), undefined variables (F821), bare except clauses (E722), missing timezone info (DTZ001, DTZ005)
- **Fix automatically**: `hatch fmt` (without --check) fixes most formatting issues automatically

### Common File Operations
- **Always check**: `tests/` directory for example CSV files when testing
- **Always check**: `example/` directory for working usage examples  
- **Key files to monitor**: 
  - `src/main.py` for core visualization logic
  - `src/config.py` when modifying configuration options
  - `tests/test_nwd.py` when adding new test scenarios

## Performance Expectations
- **Hatch command overhead**: ~0.1-0.2 seconds baseline for help/info commands
- **Environment creation**: 5-20 minutes first time (downloads dependencies), <1 second subsequently  
- **Test execution**: 5-15 seconds (with dependencies installed), 10-20 minutes (first run with environment creation)
- **Dashboard generation**: 2-10 seconds depending on data size and complexity
- **Documentation build**: 30-90 seconds for full build with image generation
- **Formatting/linting**: 0.5-2 seconds for code checking and fixes

**NEVER CANCEL long-running commands**. Build and dependency installation processes may take extended time periods but should complete successfully with appropriate timeouts.