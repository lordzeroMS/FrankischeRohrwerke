### Lüftungsanlage Integration

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

```yaml
service: switch.turn_on
data:
  entity_id: switch.lueftungsanlage_switch
  stufe: 3
```

This will set the Lüftungsanlage to stage 3, adjusting the airflow rate accordingly.