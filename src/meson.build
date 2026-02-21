gnome = import('gnome')
python = import('python')


conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
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
  'log_utils.py'
]

subdir('base')
subdir('variants/classic_sudoku')
subdir('variants/diagonal_sudoku')
subdir('screens')

install_data(sudoku_sources, install_dir: moduledir)