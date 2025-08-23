gnome = import('gnome')
python = import('python')


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
  'finished_page.py',
  'help_overlay.py'
]

install_data(sudoku_sources, install_dir: moduledir)