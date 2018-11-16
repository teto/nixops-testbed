from mininet.link import TCLink, Link, TCIntf
from mininet.log import setLogLevel, info

class AsymTCLink( TCLink ):
    """Link with potential asymmetric TC interfaces configured via opts
    Use it via passing params={ 'params1': , 'params2': }"""
    def __init__( self, node1, node2, port1=None, port2=None,
                   intfName1=None, intfName2=None,
                   addr1=None, addr2=None, **params):
         p1 = {}
         p2 = {}
         if 'params1' in params:
             p1 = params['params1']
             del params['params1']
         if 'params2' in params:
             p2 = params['params2']
             del params['params2']

         par1 = params.copy()
         par1.update(p1)
         info("par1 = %r", par1)

         par2 = params.copy()
         par2.update(p2)
         info("par2 = %r", par2)

         Link.__init__(self, node1, node2, port1=port1, port2=port2,
                       intfName1=intfName1, intfName2=intfName2,
                       cls1=TCIntf,
                       cls2=TCIntf,
                       addr1=addr1, addr2=addr2,
                       params1=par1,
                       params2=par2)


