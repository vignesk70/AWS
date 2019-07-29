BOLT_URL = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "asdfgh123" # better to read from an environment variable
DBNAME = "demodb"
BOLT_GRAPHENE = "bolt://hobby-gcbfnjjgbjfigbkeckdlcgdl.dbs.graphenedb.com:24787"
GRAPHENE_USER = "democyrus"
GRAPHENE_PASSWORD = "b.oYbLGifSOZFj.E6T2CN4uFTt2xX7Y"

from py2neo import Graph,Node
def patch_encryption():
        # Work around bug in py2neo
        from neobolt import security
        if not getattr(security.SecurityPlan.build, 'patched', None):
            old_build = security.SecurityPlan.build
            def build_encrypted(**config):
                config['encrypted'] = 1
                return old_build(**config)
            security.SecurityPlan.build = build_encrypted
            security.SecurityPlan.build.patched = True
#graph = Graph( BOLT_URL, auth=(USER, PASSWORD) )
patch_encryption()
graph = Graph( BOLT_GRAPHENE, auth=(GRAPHENE_USER, GRAPHENE_PASSWORD))
x = graph.run("match (n) return n")
print(x.to_table())
