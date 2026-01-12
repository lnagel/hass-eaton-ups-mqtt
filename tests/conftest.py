"""Test configuration for eaton_ups_mqtt."""

import sys


def pytest_configure(config):
    """Configure pytest to avoid problematic plugins."""
    # Remove problematic plugins from the plugin manager
    if hasattr(config.pluginmanager, 'unregister'):
        # Try to unregister problematic plugins
        for plugin_name in ['pytest_aiohttp', 'pytest_homeassistant_custom_component']:
            try:
                plugin = config.pluginmanager.get_plugin(plugin_name)
                if plugin:
                    config.pluginmanager.unregister(plugin)
            except Exception:
                pass
