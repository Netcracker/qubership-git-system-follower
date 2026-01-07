# Git providers

gsf performs most Git operations natively to maintain its independence from specific providers. However, some frequent actions, such as creating and deleting CI/CD variables, are implemented via the REST API, which leads to dependence on the specifics of each provider.