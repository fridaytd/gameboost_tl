# G2G Upload Tool

A tool for automating Adjust Gameboost offers price.

## Prerequisites

Before you begin, ensure you have the following installed:

### 1. Git
- Install Git from [git-scm.com](https://git-scm.com/downloads/win)
- Verify installation by running `git --version` in PowerShell

### 2. UV Package Manager
- Install UV by running this command in PowerShell:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- Restart PowerShell after installation

## Installation

1. Open PowerShell in your desired installation directory
2. Clone the repository:
   ```powershell
    git clone https://github.com/fridaytd/gameboost_tl.git
    cd gameboost_tl
   ```
3. Set up configuration:
   - Copy `keys.json` to the project directory
   - Copy `settings.env` to the project directory

## Usage

 Start the tool:
   ```powershell
   .\run.ps1
   ```
