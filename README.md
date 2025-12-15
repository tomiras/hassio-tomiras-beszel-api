# Tomiras Beszel API – Custom Home Assistant Integration

This is a **custom, modified version** of the original  
[beszel-ha Home Assistant integration](https://github.com/Ronjar/beszel-ha)  
created by **@Ronjar**.

It is **not a public fork**, but a *manual clone* (“silent fork”) that preserves
the upstream project as an `upstream` remote while allowing independent
modifications and feature development.

If you are looking for the **official integration**, please use the repository above.

---

## ⚙️ Hardware Compatibility

This custom integration extends GPU monitoring beyond what the upstream project
provides, but **GPU features currently only work on Intel-based systems**.

### Supported:
- Intel CPUs with integrated graphics (i915)
- Intel iGPU statistics exposed through:
  - intel_gpu_top
  - intel-gpu-tools
  - i915 sysfs counters
  - Beszel agent GPU telemetry (`g`, `t`, engine maps, power domains)

### Not supported:
- AMD GPUs
- NVIDIA GPUs
- ARM CPUs without Intel graphics
- Systems without `/dev/dri/card0` or i915 support

These platforms will still function for:
- CPU / RAM / Disk sensors  
- Uptime  
- Bandwidth  
- Battery  
- EFS  
…but **GPU sensors will not be created**, and this is expected behavior.

## 🔧 Custom Changes Added in This Version

- Full Intel iGPU monitoring:
  - GPU usage
  - GPU tile power draw
  - GPU package power draw
  - GPU memory stats
  - GPU temperature (best-effort)
- Intel GPU engine utilization:
  - Render / 3D
  - Blitter / Copy
  - Video
  - VideoEnhance
- Improved uptime sensor (with human-readable formatting)
- Battery sensor support
- Other personal enhancements and fixes

---

## ⚠️ Important Notes

- This is **not the official Beszel Home Assistant integration**.
- Please **do not open issues** on the upstream repository for problems found here. 
- Issues should be opened here instead.

You can find the original project at:  
➡ https://github.com/Ronjar/beszel-ha

---

## 📄 License

This project retains the **same license** as the upstream repository  
to comply with open-source requirements.  
See the [LICENSE](LICENSE) file for details.

# Installation
As this repository is not yet added in the default HACS repository you have to add the repository beforehand.

1. Go to the HACS Tab
2. Click on the three dot menu in the top right and select Custom repositories
3. Add ```https://github.com/tomiras/hassio-tomiras-beszel-api```
4. Restart HomeAssistant
5. Go to integrations, press Add integration and search for BeszelAPI
6. In the Setup Dialog use the following values
    - *URL*: The root url / IP of your Beszel instance, like http://beszel.example.com or https://beszel.example.com
    - *user*: Either your default admin username / email or (recommended) create another user with the role user and assigning the agents you want to expose to it.
    - *password*: The password to the user
7. The API will pull the data and reload every 2 minutes

Currently all machines are added, selection will be added later (you can change this yourself by creating a new user in Beszels Pocketbas and adding this user only to the machines you want to be monitored).

# Usage
After installing the following entities will exposed as sensors (more to come):
- Status (Connection)
- Uptime (Minutes)
- CPU (Percentage)
- Disk usage (Percentage)
- Temperature (°C)
- Bandwidth (Mbit/s)
- RAM (Percentage)
- Battery (Percentage)
- GPU Usage (Percentage)
- GPU Power (W)

For example if your machine is named *test*, CPU will be available as ```sensor.test_cpu```

# Examples
Here is one of my machines with the entities the integration currently exports
![Screenshot from HomeAssistant settings page of my device and its entities](/pictures/sensors.png)

And here one card I created for myself using those sensors:
![Screenshot from HomeAssistant dashboard with a card showing CPU, RAM and Disk usage as bar charts](/pictures/example_card.png)

The YAML for this card layout:
``` YAML
type: custom:vertical-stack-in-card
cards:
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-template-card
        primary: Evergreen
        icon: mdi:server
        secondary: ""
        icon_color: |-
          {% if states('binary_sensor.evergreen_status') | bool %}
            green
          {% else %}
            red
          {% endif %}
        fill_container: false
        multiline_secondary: false
        entity: binary_sensor.evergreen_status
      - type: custom:mushroom-template-card
        entity: sensor.evergreen_uptime
        icon: mdi:sort-clock-descending
        primary: "{{ (states('sensor.evergreen_uptime') | int / 1440) | int  }} Days"
        secondary: ""
        icon_color: blue
        card_mod:
          style: |
            ha-card {
              margin: 0 10px;
              align-items: end;
              box-shadow: none;
            }
  - type: custom:bar-card
    entities:
      - entity: sensor.evergreen_cpu
        name: CPU
        color: "#4caf50"
      - entity: sensor.evergreen_ram
        name: RAM
        color: "#2196f3"
      - entity: sensor.evergreen_disk
        name: Disk
        color: "#f44336"
    positions:
      indicator: "off"
```
## 🛠 Development

This repository is maintained as a “silent fork”:

- `origin` → https://github.com/tomiras/hassio-tomiras-beszel-api  
- `upstream` → https://github.com/Ronjar/beszel-ha  

To sync with upstream:
```bash
git fetch upstream
git merge upstream/main
git push origin main