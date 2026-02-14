# Pytest integration for Meson

python = import('python').find_installation('python3')

test(
  'pytest',
  python,
  args: ['-m', 'pytest', '-q', '--tb=short', 'tests'],
  workdir: meson.project_source_root(),
  suite: 'unit',
  timeout: 120,
)
