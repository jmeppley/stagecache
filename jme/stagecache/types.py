asset_types = {
    'file': {'name': 'file', 'contents':{'suff_list':['']}},
    'lastdb': {'name': 'lastdb',
               'contents': {
                   'suff_patt': '[0-9]*\.(prj|suf|bck|ssp|tis|sds|des)$',
                   'suff_list': ['.tax', '.ids'],
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
