from split_settings.tools import optional, include

include(
    'default_settings.py',
    optional('local_settings.py')
)