#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""Generic Filtering Routines"""

__author__ = "Don Allingham"

from GTK import FILL,EXPAND
import gtk
import gnome.ui
import libglade
import string
import os

import const
from RelLib import *
import GenericFilter
import intl
_ = intl.gettext

class FilterEditor:
    def __init__(self,filterdb):
        self.filterdb = GenericFilter.GenericFilterList(filterdb)
        self.filterdb.load()
        
        self.editor = libglade.GladeXML(const.filterFile,'filter_list')
        self.editor_top = self.editor.get_widget('filter_list')
        self.filter_list = self.editor.get_widget('filters')
        self.draw_filters()
        self.editor.signal_autoconnect({
            'on_add_clicked' : self.add_new_filter,
            'on_edit_clicked' : self.edit_filter,
            'on_close_clicked' : self.close_filter_editor,
            'on_delete_clicked' : self.delete_filter,
            })

    def close_filter_editor(self,obj):
        self.filterdb.save()
        self.editor_top.destroy()
        
    def draw_filters(self):
        row = 0
        self.filter_list.clear()
        for f in self.filterdb.get_filters():
            self.filter_list.append([f.get_name(),f.get_comment()])
            self.filter_list.set_row_data(row,f)
            row = row + 1

    def add_new_filter(self,obj):
        filter = GenericFilter.GenericFilter()
        filter.set_name('NoName')
        self.filter_editor(filter)

    def edit_filter(self,obj):
        sel = self.filter_list.selection
        if len(sel) != 1:
            return
        filter = self.filter_list.get_row_data(sel[0])
        self.filter_editor(GenericFilter.GenericFilter(filter))

    def delete_filter(self,obj):
        sel = self.filter_list.selection
        if len(sel) != 1:
            return
        filter = self.filter_list.get_row_data(sel[0])
        self.filterdb.get_filters().remove(filter)
        self.draw_filters()

    def filter_editor(self,filter):
        self.filter = filter
        self.glade = libglade.GladeXML(const.filterFile,'define_filter')
        self.top = self.glade.get_widget('define_filter')
        self.rule_list = self.glade.get_widget('rule_list')
        self.fname = self.glade.get_widget('filter_name')
        self.comment = self.glade.get_widget('comment')
        self.glade.signal_autoconnect({
            'on_ok_clicked' : self.on_ok_clicked,
            'on_cancel_clicked' : self.on_cancel_clicked,
            'on_delete_clicked' : self.on_delete_clicked,
            'on_add_clicked' : self.on_add_clicked,
            'on_edit_clicked' : self.on_edit_clicked,
            'on_cancel_clicked' : self.on_cancel_clicked,
            })
        self.fname.set_text(self.filter.get_name())
        self.comment.set_text(self.filter.get_comment())
        self.draw_rules()

    def draw_rules(self):
        self.rule_list.clear()
        row = 0
        for r in self.filter.get_rules():
            self.rule_list.append([r.name(),r.display_values()])
            self.rule_list.set_row_data(row,r)
            row = row + 1
            
    def on_cancel_clicked(self,obj):
        self.top.destroy()

    def on_ok_clicked(self,obj):
        n = string.strip(self.fname.get_text())
        if n == '':
            return
        self.filter.set_name(n)
        self.filter.set_comment(string.strip(self.comment.get_text()))
        for f in self.filterdb.get_filters()[:]:
            if n == f.get_name():
                self.filterdb.get_filters().remove(f)
                break
        self.filterdb.add(self.filter)
        self.draw_filters()
        self.top.destroy()
        
    def on_add_clicked(self,obj):
        self.edit_rule(None)

    def on_edit_clicked(self,obj):
        if len(self.rule_list.selection) != 1:
            return
        row = self.rule_list.selection[0]
        d = self.rule_list.get_row_data(row)
        self.edit_rule(d)

    def edit_rule(self,val):
        self.active_rule = val
        self.rule = libglade.GladeXML(const.filterFile,'add_rule')
        self.rule_top = self.rule.get_widget('add_rule')
        self.frame = self.rule.get_widget('values')
        self.rname = self.rule.get_widget('rule_name')

        self.notebook = gtk.GtkNotebook()
        self.notebook.set_show_tabs(0)
        self.notebook.set_show_border(0)
        self.notebook.show()
        self.frame.add(self.notebook)
        self.page_num = 0
        self.page = []
        self.name2page = {}
        map = {}
        list = []
        for name in GenericFilter.tasks.keys():
            cname = GenericFilter.tasks[name]
            arglist = cname.labels
            vallist = []
            tlist = []
            self.page.append((name,cname,vallist,tlist))
            table = gtk.GtkTable(2,len(arglist))
            table.show()
            pos = 0
            l2 = gtk.GtkLabel(name)
            l2.set_alignment(0,0.5)
            l2.show()
            c = gtk.GtkListItem()
            c.add(l2)
            c.set_data('d',pos)
            c.show()
            list.append(c)
            map[name] = c
            for v in arglist:
                l = gtk.GtkLabel(v)
                l.set_alignment(1,0.5)
                l.show()
                if v == 'Event':
                    t = gtk.GtkCombo()
                    t.set_popdown_strings(const.personalEvents)
                    t.set_value_in_list(1,0)
                    t.entry.set_editable(0)
                    tlist.append(t.entry)
                elif v == 'Attribute':
                    t = gtk.GtkCombo()
                    t.set_popdown_strings(const.personalAttributes)
                    t.set_value_in_list(1,0)
                    t.entry.set_editable(0)
                    tlist.append(t.entry)
                else:
                    t = gtk.GtkEntry()
                    tlist.append(t)
                t.show()
                table.attach(l,0,1,pos,pos+1,EXPAND|FILL,0,5,5)
                table.attach(t,1,2,pos,pos+1,EXPAND|FILL,0,5,5)
                pos = pos + 1
            self.notebook.append_page(table,gtk.GtkLabel(name))
            self.name2page[name] = self.page_num
            self.page_num = self.page_num + 1
        self.page_num = 0
        self.rname.disable_activate()
        self.rname.list.clear_items(0,-1)
        self.rname.list.append_items(list)
        for v in map.keys():
            self.rname.set_item_string(map[v],v)

        if self.active_rule:
            page = self.name2page[self.active_rule.name()]
            self.rname.entry.set_text(self.active_rule.name())
            self.notebook.set_page(page)
            (n,c,v,t) = self.page[page]
            r = self.active_rule.values()
            for i in range(0,len(t)):
                t[i].set_text(r[i])

        self.rname.entry.connect('changed',self.rule_changed)
        self.rule.get_widget('ok').connect('clicked',self.rule_ok)
        self.rule.get_widget('cancel').connect('clicked',self.rule_cancel)

    def on_delete_clicked(self,obj):
        if len(self.rule_list.selection) != 1:
            return
        row = self.rule_list.selection[0]
        del self.filter.get_rules()[row]
        self.draw_rules()

    def rule_changed(self,obj):
        name = obj.get_text()
        page = self.name2page[name]
        self.notebook.set_page(page)

    def rule_ok(self,obj):
        name = self.rname.entry.get_text()
        page = self.name2page[name]
        (n,c,v,t) = self.page[page]
        value_list = []
        for x in t:
            value_list.append(x.get_text())
        new_rule = c(value_list)
        if self.active_rule:
            index = self.rule_list.selection[0]
            self.filter.get_rules()[index] = new_rule
        else:
            self.filter.add_rule(new_rule)
        self.draw_rules()
        self.rule_top.destroy()
                               
    def rule_cancel(self,obj):
        self.rule_top.destroy()

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
def runTool(database,person,callback):
    FilterEditor(const.custom_filters)

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
from Plugins import register_tool

register_tool(
    runTool,
    _("Custom Filter Editor"),
    category=_("Utilities"),
    description=_("The Custom Filter Editor builds custom filters that can be used to select people included reports, exports, and other utilities.")
    )
