# 📊 Tastory Architecture Charts

This directory contains Mermaid diagrams that visualize Tastory's system architecture, workflows, and deployment processes.

## 📋 Available Charts

### 🔥 [`hot-release-workflow.md`](./hot-release-workflow.md)

**Hot Release System Architecture**

- Complete workflow for GitHub release → GCP deployment
- Shows the separation between development CI and production deployment
- Includes safety features, health checks, and rollback procedures
- Visualizes the "Think.Beyond." deployment strategy

## 🎯 How to View Charts

### **GitHub (Recommended)**

- GitHub natively renders Mermaid diagrams in markdown files
- Simply click on any `.md` file in this directory
- Charts will display with full styling and colors

### **VSCode**

1. Install the "Mermaid Preview" extension
2. Open any `.md` file with mermaid charts
3. Use `Ctrl+Shift+P` → "Mermaid Preview: Open Preview"

### **Online Mermaid Editor**

1. Copy the mermaid code from any chart
2. Go to https://mermaid.live/
3. Paste the code to edit and export

### **Local Development**

```bash
# Install mermaid CLI globally
npm install -g @mermaid-js/mermaid-cli

# Generate PNG from mermaid file
mmdc -i hot-release-workflow.md -o hot-release-workflow.png
```

## 📂 Chart Categories

### 🚀 **Deployment & CI/CD**

- `hot-release-workflow.md` - Production deployment process

### 🏗️ **Future Charts** (Coming Soon)

- System architecture overview
- Database relationships
- API endpoint mappings
- Frontend component hierarchy
- Test coverage visualization

## 🎨 Chart Styling Guide

Our charts use consistent color coding:

- **🟡 Development/Input** (`#fff3e0`) - Git operations, code changes
- **🔴 Critical/Hot Release** (`#ffebee`) - Production deployments
- **🟢 Success/Completion** (`#e8f5e8`) - Successful operations
- **🔴 Error/Warning** (`#ffcdd2`) - Failures, rollbacks
- **🔵 Information** (`#e3f2fd`) - Regular CI/testing operations

## 🔄 Updating Charts

When system architecture changes:

1. Update the relevant mermaid diagram
2. Test rendering on GitHub or mermaid.live
3. Update this README if new charts are added
4. Commit changes with descriptive messages

## 📖 Documentation Links

- **GitHub Actions Workflows**: [`../.github/workflows/README.md`](../.github/workflows/README.md)
- **Main Project README**: [`../README.md`](../README.md)
- **Test Documentation**: [`../tests/README.md`](../tests/README.md) (if exists)

---

_These visual diagrams help developers understand Tastory's architecture at a glance. Think.Beyond. traditional documentation! 📈✨_
