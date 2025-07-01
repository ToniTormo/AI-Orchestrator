"""
Common Exclusions - Expanded Version

Set of common file and directory patterns to be excluded from repository analysis.
"""

COMMON_EXCLUSIONS = {
    # Version control
    '.git',
    '.gitignore',
    '.gitattributes',
    '.gitmodules',
    '.gitkeep',
    '.hg',
    '.svn',
    'CVS',
    
    # Dependencies and package managers
    'node_modules',
    'venv',
    'env',
    '.env',
    'virtualenv',
    'dist',
    'build',
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.Python',
    '*.so',
    '*.egg',
    '*.egg-info',
    'pip-log.txt',
    'pip-delete-this-directory.txt',
    'wheels',
    'share/python-wheels',
    '*.whl',
    
    # Package managers específicos
    'vendor',  # PHP Composer, Go modules
    'Pods',  # iOS CocoaPods
    'Carthage',  # iOS Carthage
    'packages',  # .NET NuGet
    'target',  # Java Maven/Gradle
    'out',  # Varios lenguajes
    'bin',  # Binarios compilados
    'obj',  # Object files
    'lib',  # Libraries compiladas
    'deps',  # Elixir dependencies
    '_build',  # Elixir build
    'bower_components',  # Bower (legacy)
    'jspm_packages',  # JSPM
    '.yarn',  # Yarn v2+ cache
    '.pnp.*',  # Yarn PnP
    'yarn-error.log',
    'npm-debug.log*',
    'yarn-debug.log*',
    'lerna-debug.log*',
    
    # IDE and editor files
    '.idea',
    '.vscode',
    '*.swp',
    '*.swo',
    '*~',
    '.DS_Store',
    'Thumbs.db',
    '*.sublime-project',
    '*.sublime-workspace',
    '.atom/',
    '.brackets.json',
    '.editorconfig',
    '*.code-workspace',
    
    # Compiladores y herramientas específicas
    '.next',  # Next.js
    '.nuxt',  # Nuxt.js
    '.expo',  # Expo
    '.docusaurus',  # Docusaurus
    '.cache',  # Varios frameworks
    '.parcel-cache',  # Parcel bundler
    '.webpack',  # Webpack cache
    '.rollup.cache',  # Rollup cache
    'storybook-static',  # Storybook
    '.storybook/build',
    
    # Testing y coverage
    'coverage',
    '.coverage',
    'htmlcov',
    '.pytest_cache',
    '.tox',
    '.mypy_cache',
    '.ruff_cache',
    '.nyc_output',  # NYC coverage
    'lcov.info',
    'jest_coverage',
    'test-results',
    'junit.xml',
    'coverage.xml',
    
    # Análisis de código
    '.eslintcache',
    '.stylelintcache',
    'sonar-project.properties',
    '.scannerwork',  # SonarQube
    'reports',  # Varios reportes
    
    # Documentación generada
    'docs/_build',
    'docs/build',
    'site',  # MkDocs
    '_site',  # Jekyll
    'public',  # Hugo, Gatsby (cuando es generado)
    'dist-docs',
    'typedoc',
    'jsdoc',
    
    # Archivos de configuración sensibles
    '.env*',
    '*.pem',
    '*.key',
    '*.cert',
    '*.p12',
    '*.pfx',
    'secrets.json',
    'appsettings.Production.json',
    'config.production.json',
    
    # Logs y databases
    '*.log',
    '*.sqlite',
    '*.db',
    '*.sqlite3',
    '*.db3',
    'logs',
    'log',
    'combined.log',
    'error.log',
    'access.log',
    
    # Archivos de sistema y temporales
    'tmp',
    'temp',
    '*.tmp',
    '*.temp',
    '.terraform',  # Terraform
    '.terraform.lock.hcl',
    'terraform.tfstate*',
    '.vagrant',  # Vagrant
    'Vagrantfile.local',
    '.docker',  # Docker build context
    
    # Plataformas específicas
    # macOS
    '.DS_Store',
    '.AppleDouble',
    '.LSOverride',
    'Icon?',
    '._*',
    '.DocumentRevisions-V100',
    '.fseventsd',
    '.Spotlight-V100',
    '.TemporaryItems',
    '.Trashes',
    '.VolumeIcon.icns',
    '.com.apple.timemachine.donotpresent',
    
    # Windows
    'Thumbs.db',
    'Thumbs.db:encryptable',
    'ehthumbs.db',
    'ehthumbs_vista.db',
    '*.stackdump',
    '[Dd]esktop.ini',
    '$RECYCLE.BIN/',
    '*.cab',
    '*.msi',
    '*.msix',
    '*.msm',
    '*.msp',
    
    # Archivos binarios (images, audio, etc.)
    '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.svg', '*.webp', '*.ico',
    '*.tiff', '*.tif', '*.psd', '*.ai', '*.eps', '*.raw', '*.cr2', '*.nef',
    '*.mp3', '*.wav', '*.ogg', '*.flac', '*.mp4', '*.avi', '*.mov', '*.mkv',
    '*.wmv', '*.flv', '*.webm', '*.m4a', '*.aac', '*.wma',
    '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt', '*.pptx',
    '*.zip', '*.rar', '*.gz', '*.7z', '*.tar', '*.bz2', '*.xz',
    '*.exe', '*.dll', '*.so', '*.dylib', '*.app', '*.deb', '*.rpm',
    '*.ttf', '*.woff', '*.woff2', '*.eot', '*.otf',
    
    # Archivos de configuración del editor/IDE (adicionales)
    '.vimrc.local',
    '.lvimrc',
    '.exrc',
    'Session.vim',
    '.netrwhist',
    'tags',
    'TAGS',
    'cscope.*',
    '*.swp',
    '*.swo',
    '*.swn',
    
    # Contenedores y virtualización
    'docker-compose.override.yml',
    '.dockerignore',
    'Dockerfile.local',
    'docker-compose.local.yml',
    
    # Varios lenguajes específicos
    # Python adicionales
    'pip-selfcheck.json',
    'pyvenv.cfg',
    '.venv',
    'ENV',
    'env.bak',
    'venv.bak',
    'instance',
    '.webassets-cache',
    
    # JavaScript/Node adicionales
    '.grunt',
    '.lock-wscript',
    '.wafpickle-N',
    '.node_repl_history',
    '*.tgz',
    '.yarn-integrity',
    '.env.local',
    '.env.development.local',
    '.env.test.local',
    '.env.production.local',
    
    # Ruby
    '.bundle',
    'vendor/bundle',
    '.rbenv-vars',
    '.ruby-version',
    '.ruby-gemset',
    
    # Go
    'go.work',
    'go.work.sum',
    
    # Rust
    'Cargo.lock',  # Debate: algunos lo incluyen, otros no
    'target/',
    
    # C/C++
    '*.o',
    '*.a',
    '*.la',
    '*.lo',
    '*.slo',
    '*.obj',
    '*.gch',
    '*.pch',
    '*.lib',
    '*.exp',
    '*.ilk',
    '*.map',
    '*.aps',
    
    # Java adicionales
    '*.class',
    '*.jar',
    '*.war',
    '*.ear',
    '*.nar',
    'hs_err_pid*',
    
    # Archivos de backup
    '*.bak',
    '*.backup',
    '*.old',
    '*.orig',
    '*~',
    '*.swp',
    '.#*',
    '#*#',
}