from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.icon import icon_for_battery_level

from .const import DOMAIN, LOGGER

def _get_system_by_id(coordinator, sid):
    systems = coordinator.data.get("systems", [])
    for s in systems:
        if s.id == sid:
            return s
    return None

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    try:
        # Get systems and stats from coordinator data
        systems = coordinator.data.get("systems", [])
        stats_data = coordinator.data.get("stats", {})

        for system in systems:
            try:
                # Core system sensors
                entities.append(BeszelCPUSensor(coordinator, system))
                entities.append(BeszelRAMSensor(coordinator, system))
                entities.append(BeszelDiskSensor(coordinator, system))
                entities.append(BeszelBandwidthSensor(coordinator, system))
                entities.append(BeszelTemperatureSensor(coordinator, system))
                entities.append(BeszelUptimeSensor(coordinator, system))

                # Per-system stats
                system_stats = stats_data.get(system.id, {}) if stats_data else {}

                # ---- EFS sensors (existing) ----
                if system_stats and isinstance(system_stats.get("efs"), dict):
                    for disk_name in system_stats["efs"].keys():
                        entities.append(BeszelEFSDiskSensor(coordinator, system, disk_name, system_stats))
                        LOGGER.info(f"Created EFS sensor for {system.name} - {disk_name}")

                # ---- GPU sensors (NEW) ----
                # Expect system_stats["g"] = { "<gpu_key>": { "n","u","p","mu","mt" } }
                gmap = system_stats.get("g") if isinstance(system_stats, dict) else None
                if isinstance(gmap, dict) and gmap:
                    # Temps are in a flat temp map: system_stats["t"] = { label: value_C }
                    tmap = system_stats.get("t") if isinstance(system_stats.get("t"), dict) else {}

                    for gpu_key, gvals in gmap.items():
                        try:
                            gpu_name = gvals.get("n") or f"GPU {gpu_key}"
                            # Usage (%)
                            entities.append(BeszelGPUSensorUsage(coordinator, system, gpu_key, gpu_name))
                            # Power (W) - may be None for some iGPU setups
                            entities.append(BeszelGPUSensorPower(coordinator, system, gpu_key, gpu_name))
                            # Power (split)
                            entities.append(BeszelGPUSensorPowerTile(coordinator, system, gpu_key, gpu_name))
                            entities.append(BeszelGPUSensorPowerPackage(coordinator, system, gpu_key, gpu_name))
                            # Memory used / total (MB or None depending on exporter)
                            entities.append(BeszelGPUSensorMemUsed(coordinator, system, gpu_key, gpu_name))
                            entities.append(BeszelGPUSensorMemTotal(coordinator, system, gpu_key, gpu_name))
                            # Temperature (best-effort from temp map)
                            entities.append(BeszelGPUSensorTemp(coordinator, system, gpu_key, gpu_name))
                            # Engine utilizations
                            entities.append(BeszelGPUEngineRender(coordinator, system, gpu_key, gpu_name, "render"))
                            entities.append(BeszelGPUEngineBlitter(coordinator, system, gpu_key, gpu_name, "blitter"))
                            entities.append(BeszelGPUEngineVideo(coordinator, system, gpu_key, gpu_name, "video"))
                            entities.append(BeszelGPUEngineVideoEnhance(coordinator, system, gpu_key, gpu_name, "videoenhance"))
                            LOGGER.info(f"Created GPU sensors for {system.name} - {gpu_name} ({gpu_key})")
                        except Exception as ge:
                            LOGGER.error(f"Failed to create GPU sensors for {system.name} ({gpu_key}): {ge}")
                            continue

            except Exception as e:
                LOGGER.error(f"Failed to create sensors for system {getattr(system, 'name', 'unknown')}: {e}")
                continue

        LOGGER.info(f"Created {len(entities)} sensors total")
        async_add_entities(entities)

    except Exception as e:
        LOGGER.error(f"Failed to setup sensors: {e}")
        raise


class BeszelBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, system):
        super().__init__(coordinator)
        self._system_id = system.id

    @property
    def system(self):
        return _get_system_by_id(self.coordinator, self._system_id)

    @property
    def device_info(self):
        sys = self.system
        if sys is None:
            return None
        info = getattr(sys, "info", {})
        return {
            "identifiers": {(DOMAIN, sys.id)},
            "name": sys.name,
            "manufacturer": "Beszel",
            "model": info.get("m"),
            "sw_version": info.get("v"),
            "hw_version": info.get("k"),
        }

# ----------------------
# Core (existing) sensors
# ----------------------

class BeszelCPUSensor(BeszelBaseSensor):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_cpu"

    @property
    def name(self):
        return f"{self.system.name} CPU" if self.system else None

    @property
    def icon(self):
        return "mdi:memory"

    @property
    def native_value(self):
        return self.system.info.get("cpu") if self.system else None

    @property
    def native_unit_of_measurement(self):
        return "%"


class BeszelRAMSensor(BeszelBaseSensor):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_ram"

    @property
    def name(self):
        return f"{self.system.name} RAM" if self.system else None

    @property
    def icon(self):
        return "mdi:chip"

    @property
    def native_value(self):
        return self.system.info.get("mp") if self.system else None

    @property
    def native_unit_of_measurement(self):
        return "%"


class BeszelDiskSensor(BeszelBaseSensor):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_disk"

    @property
    def name(self):
        return f"{self.system.name} Disk" if self.system else None

    @property
    def icon(self):
        return "mdi:harddisk"

    @property
    def native_value(self):
        return self.system.info.get("dp") if self.system else None

    @property
    def native_unit_of_measurement(self):
        return "%"


class BeszelBandwidthSensor(BeszelBaseSensor):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_bandwidth"

    @property
    def name(self):
        return f"{self.system.name} Bandwidth" if self.system else None

    @property
    def icon(self):
        return "mdi:router-network"

    @property
    def native_value(self):
        return self.system.info.get("b") if self.system else None

    @property
    def native_unit_of_measurement(self):
        return "MB/s"


class BeszelTemperatureSensor(BeszelBaseSensor):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_temperature"

    @property
    def name(self):
        return f"{self.system.name} temperature" if self.system else None

    @property
    def native_value(self):
        return self.system.info.get("dt") if self.system else None

    @property
    def device_class(self):
        return "temperature"

    @property
    def native_unit_of_measurement(self):
        return "°C"


class BeszelUptimeSensor(BeszelBaseSensor):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_uptime"

    @property
    def name(self):
        return f"{self.system.name} uptime" if self.system else None

    @property
    def icon(self):
        return "mdi:sort-clock-descending"

    @property
    def native_value(self):
        """Return uptime in minutes (numeric) to preserve existing statistics."""
        if not self.system:
            return None
        return self.system.info.get("u")

    @property
    def native_unit_of_measurement(self):
        return "minutes"

    @property
    def suggested_display_precision(self):
        return 0

    @property
    def state_class(self):
        return "total_increasing"

    @property
    def extra_state_attributes(self):
        """Human-friendly string:
           <1h: Xm    1–23h: Hh Mm    ≥24h: Dd Hh
        """
        if not self.system:
            return {}
        minutes_total = self.system.info.get("u")
        if minutes_total is None:
            return {}

        total_minutes = int(minutes_total)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        days = hours // 24
        hours_remainder = hours % 24

        if hours < 1:
            formatted = f"{minutes}m"
        elif hours < 24:
            formatted = f"{hours}h {minutes}m"
        else:
            formatted = f"{days}d {hours_remainder}h"

        return {"formatted": formatted}


class BeszelEFSDiskSensor(BeszelBaseSensor):
    def __init__(self, coordinator, system, disk_name, stats_data):
        super().__init__(coordinator, system)
        self._disk_name = disk_name
        self._stats_data = stats_data

    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_efs_{self._disk_name}"

    @property
    def name(self):
        return f"{self.system.name} EFS {self._disk_name}" if self.system else None

    @property
    def icon(self):
        return "mdi:harddisk"

    @property
    def native_value(self):
        if not self._stats_data:
            return None

        efs_data = self._stats_data.get('efs', {})
        disk_data = efs_data.get(self._disk_name, {})

        total_space = disk_data.get('d')
        used_space = disk_data.get('du')

        # Calculate disk usage percentage
        if total_space and used_space and total_space > 0:
            return round((used_space / total_space) * 100, 2)
        return None

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def extra_state_attributes(self):
        """Return additional state attributes for the EFS disk."""
        if not self._stats_data:
            return {}

        efs_data = self._stats_data.get('efs', {})
        disk_data = efs_data.get(self._disk_name, {})

        return {
            "total_disk_space_gb": disk_data.get('d'),
            "disk_used_gb": disk_data.get('du'),
            "read_mb_s": disk_data.get('r'),
            "write_mb_s": disk_data.get('w'),
        }


# ----------------------
# GPU sensors (NEW)
# ----------------------

class _GPUBase(BeszelBaseSensor):
    """Shared helpers for GPU sensors."""

    def __init__(self, coordinator, system, gpu_key, gpu_name):
        super().__init__(coordinator, system)
        self._gpu_key = str(gpu_key)
        self._gpu_name = str(gpu_name or f"GPU {gpu_key}")

    def _system_stats(self):
        all_stats = self.coordinator.data.get("stats", {})
        return all_stats.get(self._system_id, {}) if isinstance(all_stats, dict) else {}

    def _gpu_vals(self):
        ss = self._system_stats()
        gmap = ss.get("g", {})
        if isinstance(gmap, dict):
            return gmap.get(self._gpu_key, {}) or {}
        return {}

    def _gpu_temp_value(self):
        """Try to find a GPU temp from the flat temp map."""
        ss = self._system_stats()
        tmap = ss.get("t", {})
        if not isinstance(tmap, dict):
            return None
        # Prefer keys that contain 'gpu', otherwise try to match gpu name
        lower_name = self._gpu_name.lower()
        best = None
        for k, v in tmap.items():
            kn = str(k).lower()
            if "gpu" in kn:
                best = v
                break
            if lower_name and lower_name in kn:
                best = v
        return best

    @property
    def name(self):
        sys = self.system
        if not sys:
            return None
        return f"{sys.name} {self._gpu_name} {self._label()}"

    def _label(self):
        return "Sensor"

    @property
    def icon(self):
        return "mdi:gauge"


class BeszelGPUSensorUsage(_GPUBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_usage"

    def _label(self):
        return "Usage"

    @property
    def native_value(self):
        return self._gpu_vals().get("u")

    @property
    def native_unit_of_measurement(self):
        return "%"


class BeszelGPUSensorPower(_GPUBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_power"

    def _label(self):
        return "Power"

    @property
    def icon(self):
        return "mdi:flash"

    @property
    def native_value(self):
        return self._gpu_vals().get("p")

    @property
    def native_unit_of_measurement(self):
        return "W"


class BeszelGPUSensorMemUsed(_GPUBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_mem_used"

    def _label(self):
        return "Memory Used"

    @property
    def icon(self):
        return "mdi:memory"

    @property
    def native_value(self):
        return self._gpu_vals().get("mu")

    @property
    def native_unit_of_measurement(self):
        # Adjust to "GB" if your Beszel agent reports GB instead of MB
        return "MB"


class BeszelGPUSensorMemTotal(_GPUBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_mem_total"

    def _label(self):
        return "Memory Total"

    @property
    def icon(self):
        return "mdi:memory"

    @property
    def native_value(self):
        return self._gpu_vals().get("mt")

    @property
    def native_unit_of_measurement(self):
        return "MB"


class BeszelGPUSensorTemp(_GPUBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_temp"

    def _label(self):
        return "Temperature"

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def device_class(self):
        return "temperature"

    @property
    def native_value(self):
        return self._gpu_temp_value()

    @property
    def native_unit_of_measurement(self):
        return "°C"

class BeszelGPUSensorPowerTile(_GPUBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_power_tile"

    def _label(self):
        return "GPU Tile Power"

    @property
    def icon(self):
        return "mdi:flash"

    def _power_domains(self):
        """Return any per-domain power dict if present."""
        ss = self._system_stats()
        # Heuristic: some agents expose a top-level power domain map; try common keys.
        for k in ("power", "pd", "rapl", "pwr"):
            v = ss.get(k)
            if isinstance(v, dict):
                return v
        return {}

    @property
    def native_value(self):
        # 1) Primary: per-GPU map contains tile power as 'p'
        v = self._gpu_vals().get("p")
        if isinstance(v, (int, float)):
            return v
        # 2) Fallback: scan a power-domain map for GT/GPU-specific keys
        pd = self._power_domains()
        for key in pd:
            k = str(key).lower()
            if any(s in k for s in ("gpu", "gt", "graphics", "gfx")):
                val = pd.get(key)
                if isinstance(val, (int, float)):
                    return val
        return None

    @property
    def native_unit_of_measurement(self):
        return "W"


class BeszelGPUSensorPowerPackage(_GPUBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_power_package"

    def _label(self):
        return "Package Power"

    @property
    def icon(self):
        return "mdi:cpu-64-bit"

    def _power_domains(self):
        ss = self._system_stats()
        for k in ("power", "pd", "rapl", "pwr"):
            v = ss.get(k)
            if isinstance(v, dict):
                return v
        return {}

    @property
    def native_value(self):
        # Some agents may stash package power next to GPU values (rare); try it:
        for key in ("pp", "package", "pkg"):
            v = self._gpu_vals().get(key)
            if isinstance(v, (int, float)):
                return v

        # Preferred: a top-level power-domain dict with a package/rapl domain
        pd = self._power_domains()
        for key in pd:
            k = str(key).lower()
            if any(s in k for s in ("package", "pkg", "rapl_package", "rapl:package")):
                val = pd.get(key)
                if isinstance(val, (int, float)):
                    return val
        return None

    @property
    def native_unit_of_measurement(self):
        return "W"

class _GPUEngineBase(_GPUBase):
    """Shared logic for GPU engine utilization sensors (Render/3D, Blitter, Video, VideoEnhance)."""

    # Alias map for common Intel engine names from intel_gpu_top / i915:
    _ALIASES = {
        "render": ["render", "rcs", "3d", "gfx", "render3d"],
        "blitter": ["blitter", "bcs", "copy"],
        "video": ["video", "vcs", "media", "video0"],
        "videoenhance": ["videoenhance", "vecs", "ve", "video-enhance", "video_enhance"],
    }

    def __init__(self, coordinator, system, gpu_key, gpu_name, eng_name):
        super().__init__(coordinator, system, gpu_key, gpu_name)
        self._eng_name = eng_name  # one of: render, blitter, video, videoenhance

    def _engine_map(self):
        """Return the engine utilization dict for this GPU, if present."""
        g = self._gpu_vals()
        # Try a few likely field names for engine map
        for k in ("e", "eng", "engines", "ge", "engine_util", "engine"):
            v = g.get(k)
            if isinstance(v, dict):
                return v
        return {}

    def _find_value(self):
        emap = self._engine_map()
        if not emap:
            return None
        # exact match first
        if self._eng_name in emap and isinstance(emap[self._eng_name], (int, float)):
            return emap[self._eng_name]
        # alias match
        for alias in self._ALIASES.get(self._eng_name, []):
            if alias in emap and isinstance(emap[alias], (int, float)):
                return emap[alias]
        # last resort: scan keys that contain the alias words
        for k, v in emap.items():
            if not isinstance(v, (int, float)):
                continue
            lk = str(k).lower()
            if any(alias in lk for alias in self._ALIASES.get(self._eng_name, [])):
                return v
        return None

    @property
    def native_value(self):
        return self._find_value()

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def icon(self):
        # Distinct icons per engine (purely cosmetic)
        if self._eng_name == "render":
            return "mdi:gauge"
        if self._eng_name == "blitter":
            return "mdi:content-copy"
        if self._eng_name == "video":
            return "mdi:video"
        if self._eng_name == "videoenhance":
            return "mdi:video-vintage"
        return "mdi:chip"

    def _label(self):
        return {
            "render": "Render/3D Util",
            "blitter": "Blitter Util",
            "video": "Video Util",
            "videoenhance": "VideoEnhance Util",
        }.get(self._eng_name, "Engine Util")


class BeszelGPUEngineRender(_GPUEngineBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_eng_render"


class BeszelGPUEngineBlitter(_GPUEngineBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_eng_blitter"


class BeszelGPUEngineVideo(_GPUEngineBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_eng_video"


class BeszelGPUEngineVideoEnhance(_GPUEngineBase):
    @property
    def unique_id(self):
        return f"beszel_{self._system_id}_gpu_{self._gpu_key}_eng_videoenhance"
