"""
Internationalization (i18n) support for ClamUI.

This module initializes gettext for the ClamUI application and exports
the translation functions used throughout the codebase.

Usage:
    from ..core.i18n import _, ngettext, N_, pgettext

    label.set_text(_("Scan Complete"))
    label.set_text(_("Found {count} threats").format(count=n))
    msg = ngettext("{n} file scanned", "{n} files scanned", count).format(n=count)

    # Module-level constants (deferred translation):
    ITEMS = [N_("Scan"), N_("Update")]
    # At display time: _(item)
"""

import gettext
import os

DOMAIN = "clamui"

__all__ = ["DOMAIN", "N_", "_", "ngettext", "pgettext"]


def _get_locale_dir() -> str | None:
    """
    Determine the locale directory based on the runtime context.

    Checks in order:
    1. AppImage: $APPDIR/usr/share/locale
    2. Flatpak: /app/share/locale
    3. Development / pip install: src/locale relative to this file
    4. System: /usr/share/locale (fallback)

    Returns:
        Path to the locale directory, or None to use system default.
    """
    # AppImage bundles locale in $APPDIR/usr/share/locale
    appdir = os.environ.get("APPDIR")
    if appdir:
        locale_dir = os.path.join(appdir, "usr", "share", "locale")
        if os.path.isdir(locale_dir):
            return locale_dir

    # Flatpak uses /app/share/locale
    if os.path.exists("/.flatpak-info"):
        locale_dir = "/app/share/locale"
        if os.path.isdir(locale_dir):
            return locale_dir

    # Development / editable install: src/locale relative to this module
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dev_locale = os.path.join(src_dir, "locale")
    if os.path.isdir(dev_locale):
        return dev_locale

    # System install fallback
    system_locale = "/usr/share/locale"
    if os.path.isdir(system_locale):
        return system_locale

    return None


def _init_gettext():
    """Initialize gettext with the appropriate locale directory."""
    locale_dir = _get_locale_dir()

    if locale_dir:
        gettext.bindtextdomain(DOMAIN, locale_dir)

    gettext.textdomain(DOMAIN)


# Initialize on import
_init_gettext()

# Export translation functions
_ = gettext.gettext
ngettext = gettext.ngettext
pgettext = gettext.pgettext
_TRANSLATION_FUNCTIONS = (_, ngettext, pgettext)

# N_ marks strings for extraction by xgettext but returns them unchanged.
# The actual translation happens when _() is called at display time.
# This must NOT call gettext.gettext -- it's an identity function.


def N_(message: str) -> str:
    """Mark a string for translation extraction without translating it."""
    return message
