from Products.CMFCore.utils import getToolByName


def import_various(context):
    portal = context.getSite()
    action = context.readDataFile('ftw.lawgiver.various.txt')
    action = action.strip() if action else None

    if action == 'uninstall':
        uninstall_controlpanel(portal)


def uninstall_controlpanel(portal):
    controlpanel = getToolByName(portal, 'portal_controlpanel')
    controlpanel.unregisterConfiglet('lawgiver-listing')
