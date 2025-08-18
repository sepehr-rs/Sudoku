pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'sudokugame')
gnome = import('gnome')
python = import('python')

blueprint_compiler = find_program('blueprint-compiler', required: true)

blueprint_files = files(
  'window.blp',
  'gtk/help-overlay.blp',
  'gtk/finished-overlay.blp',
)

compiled_ui_dir_name = 'compiled_ui_files'

compiled_blueprints = custom_target('compiled_blueprints',
  input: blueprint_files,
  output: compiled_ui_dir_name,
  command: [blueprint_compiler, 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@']
)

gnome.compile_resources('sudokugame',
  'sudokugame.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: [compiled_blueprints],
  source_dir: [meson.current_source_dir(), compiled_blueprints.full_path()],
)

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'sudokugame.in',
  output: 'sudokugame',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

sudoku_sources = [
  '__init__.py',
  'main.py',
  'application.py',
  'window.py',
  'game_board.py',
  'game_manager.py',
  'sudoku_cell.py',
  'help_dialog.py',
  'difficulty_selection_dialog.py',
  'ui_helpers.py',
  'finished_overlay.py',
]

install_data(sudoku_sources, install_dir: moduledir)
