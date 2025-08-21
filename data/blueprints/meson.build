blueprint_compiler = find_program('blueprint-compiler', required: true)

blueprint_files = files(
  'window.blp',
  'help-overlay.blp',
  'finished-page.blp',
  'how-to-play-dialog.blp'
)

compiled_ui_files = []
foreach blueprint : blueprint_files
  ui_file = custom_target(
    blueprint.full_path().split('/')[-1].replace('.blp', '.ui'),
    input: blueprint,
    output: '@BASENAME@.ui',
    command: [blueprint_compiler, 'compile', '--output', '@OUTPUT@', '@INPUT@'],
    install: false,
  )
  compiled_ui_files += ui_file
endforeach

compiled_blueprints = custom_target(
  'all_compiled_blueprints',
  output: 'blueprints_compiled.stamp',
  depends: compiled_ui_files,
  command: ['touch', '@OUTPUT@'],
)