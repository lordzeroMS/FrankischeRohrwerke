### FRÄNKISCHE ROHRWERKE Lüftungsanlage Integration

This Home Assistant integration allows you to monitor and control your Lüftungsanlage (ventilation system) using Home Assistant. You can configure the IP address of your Lüftungsanlage through the Home Assistant UI and control the ventilation stages (1-4).

#### Features
- Monitor the current state of the Lüftungsanlage.
- Control the Lüftungsanlage stages (1-4).

### Installation Instructions

1. **Download the Integration:**
   Clone or download the repository and place the `lueftungsanlage` folder in your `custom_components` directory.

2. **Install Required Packages:**
   Ensure you have the required Python packages installed. You can install them using `pip`:
   ```sh
   pip install xmltodict homeassistant
   ```

3. **Configure the Integration:**
   - Go to the Home Assistant UI.
   - Navigate to `Configuration` > `Integrations`.
   - Click on the `+ Add Integration` button.
   - Search for `Lüftungsanlage` and follow the prompts to configure the IP address of your Lüftungsanlage.

### Usage Examples

#### Monitoring the Lüftungsanlage

Once the integration is set up, you can monitor the Lüftungsanlage's current state through the Home Assistant UI. The sensor will display the current airflow rate.

#### Controlling the Lüftungsanlage

You can control the Lüftungsanlage stages (1-4) using the switch entity created by the integration. For example, to set the Lüftungsanlage to stage 3, you can use the following service call in Home Assistant:

This will set the Lüftungsanlage to stage 3, adjusting the airflow rate accordingly.

### Tested Devices

This integration has been tested on the following devices:
- profi-air® 250

### Integration with HACS

To integrate this custom component with HACS (Home Assistant Community Store):

1. **Add the Repository to HACS:**
   - Go to the HACS section in Home Assistant.
   - Click on the `+` button to add a new repository.
   - Select `Custom Repositories`.
   - Enter the URL of the repository and select the category as `Integration`.

2. **Install the Integration:**
   - After adding the repository, find the `Lüftungsanlage` integration in the HACS store.
   - Click on `Install`.

3. **Configure the Integration:**
   - Follow the same configuration steps as mentioned above to set up the integration in Home Assistant.