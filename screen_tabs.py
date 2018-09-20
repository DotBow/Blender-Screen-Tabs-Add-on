'''
Copyright (C) 2018 Oleg Stepanov
stepanovoleg.dev@gmail.com

Created by Oleg Stepanov

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
	'name': 'Screen Tabs',
	'description': 'Screen Tabs provide a more consistent and nice way to interact with screens in Info Header.',
	'author': 'Oleg Stepanov',
	'version': (1, 3, 2),
	'blender': (2, 79, 0),
	'location': 'Info Header',
	'wiki_url': 'https://blenderartists.org/t/screen-tabs-1-2-add-on-for-2-79-a-la-workspace-tabs-in-2-8/1117586',
	'category': 'UI' }


import bpy
from bpy.types import Operator, PropertyGroup, Header, Menu, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty, PointerProperty, EnumProperty, BoolVectorProperty, FloatProperty
from bpy.app.handlers import persistent
from collections import OrderedDict


stats_icons = OrderedDict([
	('Verts:', 'VERTEXSEL'),
	('Edges:', 'EDGESEL'),
	('Faces:', 'FACESEL'),
	('Tris:', 'MOD_TRIANGULATE'),
	('Bones:', 'BONE_DATA'),
	('Objects:', 'OUTLINER_OB_GROUP_INSTANCE'),
	('Lamps:', 'LAMP_SUN'),
	('Mem:', 'DISK_DRIVE')])


object_type_icons = OrderedDict([
	('MESH', 'OUTLINER_OB_MESH'),
	('CURVE', 'OUTLINER_OB_CURVE'),
	('SURFACE', 'OUTLINER_OB_SURFACE'),
	('META', 'OUTLINER_OB_META'),
	('FONT', 'OUTLINER_OB_FONT'),
	('ARMATURE', 'OUTLINER_OB_ARMATURE'),
	('LATTICE', 'OUTLINER_OB_LATTICE'),
	('EMPTY', 'OUTLINER_OB_EMPTY'),
	('SPEAKER', 'OUTLINER_OB_SPEAKER'),
	('CAMERA', 'OUTLINER_OB_CAMERA'),
	('LAMP', 'OUTLINER_OB_LAMP')])


def get_stat_value(start, stats):
	return stats.partition(start)[2].partition(' ')[0]


class ScreenTabsPrefs(AddonPreferences):
	bl_idname = __name__

	menu_draw_type = EnumProperty(
		items = (('TEXT', 'Text', '', 0),
				 ('ICONS', 'Icons', '', 1)),
		name = 'Menu Draw Type',
		default = 'ICONS')

	stats_draw_type = EnumProperty(
		items = (('TEXT', 'Text', '', 0),
				 ('ICONS', 'Icons', '', 1)),
		name = 'Statistics Draw Type',
		default = 'ICONS')

	tab_draw_type = EnumProperty(
		items = (('TEXT', 'Text', '', 0),
				 ('ICONS', 'Icons', '', 1)),
		name = 'Tab Draw Type',
		default = 'TEXT')

	scene_block_width = FloatProperty(
		name = 'Scene Block Width',
		default = 80,
		subtype = 'PERCENTAGE',
		min = 20,
		max = 200)

	tab_name_length = IntProperty(
		name = 'Tab Name Length',
		default = 1,
		min = 1)

	tab_width = FloatProperty(
		name = 'Tab Width',
		default = 100,
		subtype = 'PERCENTAGE',
		min = 20,
		max = 200)

	trim_tab_names = BoolProperty(
		name = 'Trim Tab Names',
		default = False)

	def draw(self, context):
		layout = self.layout
		column = layout.column()

		column.prop(self, 'menu_draw_type')
		column.prop(self, 'stats_draw_type')
		column.prop(self, 'tab_draw_type')

		if self.tab_draw_type == 'TEXT':
			column.separator()
			column.prop(self, 'trim_tab_names')
			sub_column = column.column()

			if not self.trim_tab_names:
				sub_column.active = False

			sub_column.prop(self, 'tab_name_length')

		column.separator()
		column.prop(self, 'scene_block_width')
		column.prop(self, 'tab_width')


class TabProps(bpy.types.PropertyGroup):
	index = IntProperty(default = -1)
	icon = StringProperty(default = 'NONE')


@persistent
def set_props_on_load(dummy):
	bpy.context.scene.edit_tabs = False
	bpy.ops.scene.cleanup_names()


def init_tabs_indices():
	shift = 0

	for (i, screen) in enumerate(bpy.data.screens):
		if screen.name.startswith('temp'):
			shift -= 1
			continue

		screen.tab.index = i + shift


class SetTab(Operator):
	bl_idname = 'scene.set_tab'
	bl_label = 'Switch Tab'
	bl_options = {'INTERNAL'}

	name = StringProperty()

	def execute(self, context):
		if context.window.screen.name != self.name:
			context.window.screen = bpy.data.screens[self.name]

		return {'FINISHED'}


class MoveTab(Operator):
	bl_idname = 'scene.move_tab'
	bl_label = ''
	bl_description = 'Reorder tab'
	bl_options = {'INTERNAL'}

	dir = IntProperty()

	def execute(self, context):
		active_tab = context.window.screen.tab
		active_name = context.window.screen.name

		old_index = active_tab.index
		new_index = old_index + self.dir

		max_index = len(bpy.data.screens) - 1

		if (new_index < 0):
			for screen in bpy.data.screens:
				if screen.name.startswith('temp'):
					continue

				if screen.name != active_name:
					screen.tab.index -= 1

			active_tab.index = max_index
			return {'FINISHED'}

		if (new_index > max_index):
			for screen in bpy.data.screens:
				if screen.name.startswith('temp'):
					continue

				if screen.name != active_name:
					screen.tab.index += 1

			active_tab.index = 0
			return {'FINISHED'}

		active_tab.index = new_index

		for screen in bpy.data.screens:
			if screen.name.startswith('temp'):
				continue

			if screen.tab.index == new_index and screen.name != active_name:
				screen.tab.index = old_index
				return {'FINISHED'}

		return {'FINISHED'}


class DelTab(Operator):
	bl_idname = 'scene.del_tab'
	bl_label = 'Delete Tab'
	bl_description = 'Delete tab'
	bl_options = {'INTERNAL'}

	def execute(self, context):
		del_index = context.window.screen.tab.index
		bpy.ops.screen.delete()

		if len(bpy.data.screens) - 1 == 0:
			return {'FINISHED'}
		else:
			for (i, screen) in enumerate(bpy.data.screens):
				if screen.name.startswith('temp'):
					continue

				if screen.tab.index >= del_index:
					screen.tab.index -= 1

		return {'FINISHED'}


class AddTab(Operator):
	bl_idname = 'scene.add_tab'
	bl_label = 'Duplicate Tab'
	bl_description = 'Duplicate tab'
	bl_options = {'INTERNAL'}

	def execute(self, context):
		bpy.ops.screen.new()

		for (i, screen) in enumerate(bpy.data.screens):
			if screen.name.startswith('temp'):
				continue

			if screen.tab.index == -1:
				screen.tab.index = len(bpy.data.screens) - 1
				return {'FINISHED'}

		return {'FINISHED'}


class INFO_HT_header(Header):
	bl_space_type = 'INFO'

	def draw(self, context):
		layout = self.layout

		window = context.window
		scene = context.scene
		rd = scene.render
		addon_prefs = context.user_preferences.addons[__name__].preferences

		row = layout.row(align=True)
		row.template_header()

		layout.separator()
		INFO_MT_editor_menus.draw_collapsible(context, layout)
		layout.separator()

		if window.screen.show_fullscreen:
			layout.operator('screen.back_to_previous', icon = 'SCREEN_BACK', text = 'Back to Previous')
		else:
			#layout.template_ID(context.window, 'screen', new='screen.new', unlink='screen.delete')
			row = layout.row()
			row.scale_x = addon_prefs.scene_block_width * 0.01
			row.template_ID(context.screen, 'scene', new = 'scene.new', unlink = 'scene.delete')

			### Draw tabs ###
			layout.separator()
			tabs = [[None, None]] * len(bpy.data.screens)

			for (i, screen) in enumerate(bpy.data.screens):
				if screen.name.startswith('temp'):
					continue

				if screen.tab.index < 0:
					init_tabs_indices()

				tabs[screen.tab.index] = [screen.name, screen.tab.icon]

			active_name = window.screen.name
			row = layout.row(True)

			for name, icon in tabs:
				if name == None:
					continue

				is_active = (active_name == name)

				if (scene.edit_tabs and is_active):
					row.alert = is_active
					row.operator('scene.move_tab', text = '', icon = 'TRIA_LEFT').dir = -1
					row.operator('scene.move_tab', text = '', icon = 'TRIA_RIGHT').dir = 1

					if icon == 'NONE':
						icon = 'BLANK1'

					row.operator('window.show_icons', text = '', icon = icon).old_icon = icon
					row.prop(window.screen, 'name', text = '')
					row.operator('scene.del_tab', text = '', icon='X')
					row.operator('scene.add_tab', text = '', icon='ZOOMIN')
					row.alert = False
				else:
					display_name = name

					if addon_prefs.tab_draw_type == 'ICONS':
						display_name = ''

						if icon == 'NONE':
							icon = 'ERROR'
					else:
						if (addon_prefs.trim_tab_names):
							display_name = name[0 : addon_prefs.tab_name_length]

					row.scale_x = addon_prefs.tab_width * 0.01

					if is_active:
						row.prop(scene, 'active_tab', text = display_name, icon = icon, toggle = True)
					else:
						row.operator('scene.set_tab', text = display_name, icon = icon).name = name

		### Draw render engine ###
		layout.separator()

		if rd.has_multiple_engines:
			row = layout.row()
			row.scale_x = 0.9
			row.prop(rd, 'engine', text='')

		layout.separator()
		layout.template_running_jobs()
		layout.template_reports_banner()
		row = layout.row(align=True)

		if bpy.app.autoexec_fail is True and bpy.app.autoexec_fail_quiet is False:
			row.label('Auto-run disabled', icon='ERROR')
			if bpy.data.is_saved:
				props = row.operator('wm.revert_mainfile', icon='SCREEN_BACK', text='Reload Trusted')
				props.use_scripts = True

			row.operator('script.autoexec_warn_clear', text='Ignore')

			# include last so text doesn't push buttons out of the header
			row.label(bpy.app.autoexec_fail_message)
			return

		### Draw statistics ###
		row = layout.row(True)

		if addon_prefs.stats_draw_type == 'TEXT':
			row.label(text = scene.statistics(), translate = False)
		elif addon_prefs.stats_draw_type == 'ICONS':
			row.scale_x = 0.9
			stats = scene.statistics().replace('Mem: ', 'Mem:') + ' '
			i = 0

			if scene.edit_tabs:
				for key, val in stats_icons.items():
					row.prop(scene, 'stat_flags', index = i, text = key.replace(':', ''), icon = val)
					i += 1
					continue

				row.prop(scene, 'stat_flags', index = 7, text = 'Object Name', icon = 'OBJECT_DATA')
			else:
				for key, val in stats_icons.items():
					stat_value = get_stat_value(key, stats)

					if stat_value and scene.stat_flags[i]:
						if key == 'Mem:':
							stat_value = str(round(float(stat_value[:-1]))) + 'M'

						row.label(stat_value, icon = val)

					i += 1

				active = scene.objects.active

				if active and scene.stat_flags[7]:
					row.label(active.name, icon = object_type_icons.get(active.type))


class INFO_MT_editor_menus(Menu):
	bl_idname = 'INFO_MT_editor_menus'
	bl_label = ''

	def draw(self, context):
		self.draw_menus(self.layout, context)

	@staticmethod
	def draw_menus(layout, context):
		scene = context.scene
		rd = scene.render
		addon_prefs = context.user_preferences.addons[__name__].preferences

		if addon_prefs.menu_draw_type == 'TEXT':
			layout.menu('INFO_MT_file')

			if rd.use_game_engine:
				layout.menu('INFO_MT_game')
			else:
				layout.menu('INFO_MT_render')

			layout.menu('INFO_MT_window')
			layout.menu('INFO_MT_help')
		elif addon_prefs.menu_draw_type == 'ICONS':
			layout.menu('INFO_MT_file', icon = 'FILESEL', text = '')

			if rd.use_game_engine:
				layout.menu('INFO_MT_game', icon = 'RENDER_STILL', text = '')
			else:
				layout.menu('INFO_MT_render', icon = 'RENDER_STILL', text = '')

			layout.menu('INFO_MT_window', icon = 'SPLITSCREEN', text = '')
			layout.menu('INFO_MT_help', icon = 'HELP', text = '')


def get_icons():
	items = []
	icons = bpy.types.UILayout.bl_rna.functions['prop']\
		.parameters['icon'].enum_items.keys()

	for icon in icons:
		if 'MATCAP_' in icon or \
		   'COLORSET_' in icon or\
		   'SCULPT_DYNTOPO' in icon or\
		   'BLANK1' in icon:
		   continue

		items.append(icon)

	items[0] = 'BLANK1'
	return items


class ShowIcons(Operator):
	bl_idname = 'window.show_icons'
	bl_label = 'Show Icon'
	bl_description = 'Change tab icon'
	bl_options = {'INTERNAL'}

	old_icon = StringProperty()

	def draw(self, context):
		screen = bpy.context.window.screen
		layout = self.layout
		box = layout.box()

		row = box.row()
		row.alignment = 'LEFT'
		row.operator('scene.set_tab', text = screen.name, icon = screen.tab.icon)

		row.alignment = 'EXPAND'
		row.prop(context.scene, 'icon_search', text = '', icon = 'VIEWZOOM')

		box = layout.box()
		column = box.column(True)
		row = column.row(True)

		i = 0

		for icon in get_icons():
			icon_search = context.scene.icon_search

			if icon_search:
				if icon_search.lower() not in icon.lower():
					continue

			row.operator('scene.set_icon', text = '', icon = icon, emboss = icon == screen.tab.icon).icon = icon

			i += 1

			if i % 25 == 0:
				row = column.row(True)

		if i == 0:
			row.alignment = 'CENTER'
			row.label('No icons were found')

	def execute(self, context):
		return {'FINISHED'}

	def check(self, context):
		return True

	def cancel(self, context):
		bpy.ops.scene.set_icon(icon = self.old_icon)
		return None

	def invoke(self, context, event):
		wm = context.window_manager
		ui_scale = context.user_preferences.view.ui_scale
		return wm.invoke_props_dialog(self, width = 500 * ui_scale)


class SetIcon(Operator):
	bl_idname = 'scene.set_icon'
	bl_label = 'Set Icon'
	bl_description = 'Change tab icon'
	bl_options = {'INTERNAL'}

	icon = StringProperty()

	def execute(self, context):
		tab = bpy.context.window.screen.tab

		if self.icon == 'BLANK1':
			self.icon = 'NONE'

		tab.icon = self.icon
		return {'FINISHED'}


# Clean up screen names when updating from version 1.2 inclusive
class CleanupNames(Operator):
	bl_idname = 'scene.cleanup_names'
	bl_label = 'Cleanup Screen Names'
	bl_options = {'REGISTER'}

	def execute(self, context):
		shift = 0

		for (i, screen) in enumerate(bpy.data.screens):
			if screen.name.startswith('temp'):
				shift -= 1
				continue

			try:
				name_parts = screen.name.split('#')
				screen.tab.icon = name_parts[1]
				screen.name = name_parts[2]
			except:
				continue

		return {'FINISHED'}


def screen_tabs_menu(self, context):
	scene = context.scene
	layout = self.layout

	layout.separator()
	layout.prop(scene, 'edit_tabs')


def set_active_tab(self, value):
	self['active_tab'] = True


def register():
	bpy.utils.register_module(__name__)

	bpy.types.Screen.tab = PointerProperty(
		type = TabProps)

	bpy.types.Scene.edit_tabs = BoolProperty(
		name = 'Edit Screen Tabs',
		default = False)

	bpy.types.Scene.icon_search = StringProperty(
		options = {'TEXTEDIT_UPDATE'})

	bpy.types.Scene.stat_flags = BoolVectorProperty(
		size = 8,
		default = (True, True, True, True, True, True, True, True))

	bpy.types.Scene.active_tab = BoolProperty(
		default = True,
		set = set_active_tab)

	bpy.app.handlers.load_post.append(set_props_on_load)
	bpy.types.INFO_MT_window.append(screen_tabs_menu)


def unregister():
	bpy.utils.unregister_module(__name__)

	del bpy.types.Screen.tab
	bpy.app.handlers.load_post.remove(set_props_on_load)
	bpy.types.INFO_MT_window.remove(screen_tabs_menu)

	import bl_ui
	bpy.utils.register_class(bl_ui.space_info.INFO_HT_header)
