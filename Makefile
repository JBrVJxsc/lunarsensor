.EXPORT_ALL_VARIABLES:

# Define venv directory
VENV_DIR := venv
PYTHON := python3
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip
VENV_UVICORN := $(VENV_DIR)/bin/uvicorn

all: install run

# Create virtual environment if it doesn't exist
venv:
	test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)

install: venv
	$(VENV_PIP) install -r requirements.txt

run: SENSOR_DEBUG=0
run: PORT=80
run: HOST=::
run: UVICORN=$(VENV_UVICORN)
run:
	test -f /bin/launchctl && sudo launchctl bootout system/org.apache.httpd 2>/dev/null || true
	sudo -E $(UVICORN) --host $(HOST) --port $(PORT) --reload lunarsensor:app
