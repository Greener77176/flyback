import gnome, gobject, gtk, gtk.glade, os, sys

import backup
import create_backup_gui
import manage_backup_gui
import settings
import util

  
RUN_FROM_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

  
def echo(*args):
  print 'echo', args

class GUI(object):

  def close(self, a=None, b=None):
    self.main_window.hide()
    self.unregister_gui(self)
    
  def open_backup(self,a=None,b=None,c=None):
    treeview_backups_widget = self.xml.get_widget('treeview_backups')
    model, entry = treeview_backups_widget.get_selection().get_selected()
    if entry and model.get_value(entry, 2):
      uuid = model.get_value(entry, 3)
      host = model.get_value(entry, 4)
      path = model.get_value(entry, 5)
      if uuid and host and path:
        print 'opening... drive:%s'%uuid, 'path:%s'%path
        self.register_gui( manage_backup_gui.GUI(self.register_gui, self.unregister_gui, uuid, host, path) )
      else:
        print 'creating a new archive...'
        self.register_gui( create_backup_gui.GUI(self.register_gui, self.unregister_gui) )
      self.close()

  def update_buttons(self,a=None):
    model, entry = a.get_selection().get_selected()
    available = entry and model.get_value(entry, 2)
    if available:
      self.xml.get_widget('button_open').set_sensitive(True)
    else:
      self.xml.get_widget('button_open').set_sensitive(False)

  def __init__(self, register_gui, unregister_gui):

    self.register_gui = register_gui
    self.unregister_gui = unregister_gui
  
    self.xml = gtk.glade.XML( os.path.join( RUN_FROM_DIR, 'glade', 'select_backup.glade' ) )
    self.main_window = self.xml.get_widget('select_backup_gui')
    self.main_window.connect("delete-event", self.close )
    icon = self.main_window.render_icon(gtk.STOCK_HARDDISK, gtk.ICON_SIZE_BUTTON)
    self.main_window.set_icon(icon)
    self.main_window.set_title('%s v%s - Select Backup' % (settings.PROGRAM_NAME, settings.PROGRAM_VERSION))
    
    # buttons
    self.xml.get_widget('button_cancel').connect('clicked', self.close)
    self.xml.get_widget('button_open').connect('clicked', self.open_backup)
    
    # setup list
    treeview_backups_model = gtk.ListStore( gtk.gdk.Pixbuf, str, bool, str, str, str )
    treeview_backups_widget = self.xml.get_widget('treeview_backups')
    renderer = gtk.CellRendererPixbuf()
    renderer.set_property('xpad', 4)
    renderer.set_property('ypad', 4)
    treeview_backups_widget.append_column( gtk.TreeViewColumn('', renderer, pixbuf=0) )
    renderer = gtk.CellRendererText()
    renderer.set_property('xpad', 16)
    renderer.set_property('ypad', 16)
    treeview_backups_widget.append_column( gtk.TreeViewColumn('', renderer, markup=1) )
    treeview_backups_widget.set_headers_visible(False)
    treeview_backups_widget.set_model(treeview_backups_model)
    treeview_backups_widget.connect( 'row-activated', self.open_backup )
    treeview_backups_widget.connect( 'cursor-changed', self.update_buttons )
    treeview_backups_widget.connect( 'move-cursor', self.update_buttons )
    
    treeview_backups_model.clear()
    for t in backup.get_known_backups():
      paths = backup.get_dev_paths_for_uuid(t['uuid'])
      drive_name = 'UUID: '+ t['uuid']
      for path in paths:
        if 'disk/by-id' in path:
          drive_name = path[path.index('disk/by-id')+11:]
      s = "<b>Drive:</b> %s\n<b>Source:</b> <i>%s</i>:%s\n" % (util.pango_escape(drive_name), util.pango_escape(t['host']), util.pango_escape(t['path']))
      if backup.is_dev_present(t['uuid']) and backup.get_hostname()==t['host']:
        s += "<b>Status:</b> Drive is available and ready for backups"
      else:
        if backup.is_dev_present(t['uuid']) and backup.get_hostname()!=t['host']:
          s += "<b>Status:</b> Backup was created on another computer (available for export only)"
        else:
          s += "<b>Status:</b> Drive is unavailable (please attach)"
      icon = self.main_window.render_icon(gtk.STOCK_HARDDISK, gtk.ICON_SIZE_DIALOG)
      if not backup.is_dev_present(t['uuid']):
        icon2 = icon.copy()
        icon.saturate_and_pixelate(icon2, 0.0, False)
        icon = icon2
      treeview_backups_model.append( (icon, s, backup.is_dev_present(t['uuid']), t['uuid'], t['host'], t['path']) )
    treeview_backups_model.append( (self.main_window.render_icon(gtk.STOCK_ADD, gtk.ICON_SIZE_DIALOG), '(create a new backup)', True, None, None, None) )

    self.main_window.show()
    
