gnome = import('gnome')
python = import('python')


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

subdir('core')
subdir('shared')
subdir('screens')
subdir('variants/classic_sudoku')
subdir('variants/diagonal_sudoku')

install_data(sudoku_sources, install_dir: moduledir)
