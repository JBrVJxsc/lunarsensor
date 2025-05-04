# Copy the service file to the systemd directory
sudo cp lunarsensor.service /etc/systemd/system/

# Set the proper permissions for the service file
sudo chmod 644 /etc/systemd/system/lunarsensor.service

# Reload the systemd daemon to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable lunarsensor.service

# Start the service immediately (optional)
sudo systemctl start lunarsensor.service
