subdir('blueprints')

desktop_file = i18n.merge_file(
        input: 'io.github.sepehr_rs.Sudoku.desktop.in',
       output: 'io.github.sepehr_rs.Sudoku.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

gnome.compile_resources('sudokugame',
  'sudokugame.gresource.xml.in',
  gresource_bundle: true,
  dependencies: compiled_blueprints,
  source_dir: meson.current_build_dir(),
  install: true,
  install_dir: pkgdatadir
)

appstream_file = i18n.merge_file(
        input: 'io.github.sepehr_rs.Sudoku.metainfo.xml.in',
       output: 'io.github.sepehr_rs.Sudoku.metainfo.xml',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'metainfo')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util, args: ['validate', appstream_file])
endif

install_data('io.github.sepehr_rs.Sudoku.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file',
       compile_schemas,
       args: ['--strict', '--dry-run', meson.current_source_dir()])
endif

subdir('icons')