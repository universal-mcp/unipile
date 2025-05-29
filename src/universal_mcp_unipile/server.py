
from universal_mcp.servers import SingleMCPServer
from universal_mcp.integrations import AgentRIntegration, ApiKeyIntegration
from universal_mcp.stores import EnvironmentStore

from universal_mcp_unipile.app import UnipileApp

env_store = EnvironmentStore()
integration_instance = AgentRIntegration(name="unipile", store=env_store)
app_instance = UnipileApp(integration=integration_instance)

mcp = SingleMCPServer(
    app_instance=app_instance,
)

if __name__ == "__main__":
    mcp.run()


