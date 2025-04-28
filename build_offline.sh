#!/bin/bash

# Create a directory for the offline build
mkdir -p rimu_offline
cd rimu_offline

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r ../requirements.txt

# Copy Python files
cp ../app.py .
cp ../rimu_config_watching.json .

# Build frontend
cd ../frontend
npm install
npm run build

# Copy frontend build to rimu_offline
cp -r build ../rimu_offline/frontend

# Create a README with instructions
cat > ../rimu_offline/README.md << EOL
# Offline Build Instructions

## Backend Setup
1. Create a Python virtual environment:
   \`\`\`bash
   python3 -m venv venv
   source venv/bin/activate
   \`\`\`

2. Install dependencies:
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. Run the application:
   \`\`\`bash
   python app.py
   \`\`\`

## Frontend
The frontend is already built and ready to serve. The built files are in the \`frontend\` directory.

## Running the Application
1. Start the backend server
2. Serve the frontend files using any static file server
EOL

# Create a requirements.txt in the offline build
pip freeze > ../rimu_offline/requirements.txt

echo "Build completed! The rimu_offline directory contains everything needed to run the application offline." 