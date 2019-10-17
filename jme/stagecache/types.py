asset_types = {
    'file': {'name': 'file', 'contents':{'suff_list':['']}},
    'lastdb': {'name': 'lastdb',
               'contents': {
                   'suff_patt': '[0-9]*\.(prj|suf|bck|ssp|tis|sds|des)$',
               }
              },
    'taxdump': {'name': 'taxdump',
                'contents': {
                    'suff_list': ['/names.dmp', '/nodes.dmp']
                }
               },
    'bwadb': {'name': 'bwadb',
              'contents': {
                  'suff_patt': '\.[a-z]+$'
              }
             },
    'prefix': {'name': 'prefix',
               'contents': {'suff_patt': '[^/]*$'}
              },
}

def cleanup_asset_types(asset_types):
    for name, type_def in asset_types.items():
        # add name to def, so we don't have to keep track
        type_def['name'] = name

        # if suff_xxxx definitions are top level, move to contents
        for key in type_def:
            if key.startswith('suff_'):
                type_def.setdefault('contents', {})[key] = type_def[key]

