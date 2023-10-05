# Select Star dbt Impact Report

## Overview


## Before you start

- **Select Star API Token**: Access token to use the APIs
- **Select Star Datasource GUID**: The GUID of the datasource this repository is connected to

## Configuration

1. Create [repository secrets](https://github.com/Azure/actions-workflow-samples/blob/master/assets/create-secrets-for-GitHub-workflows.md#creating-secrets) in your repository:

   - `SELECTSTAR_API_TOKEN` with the value of the API access token.

2. Add our GitHub Action to your workflow:

   1. Create a workflow file in your repository `.github/workflows/select-star-impact-report.yml`
 
   2. Add the following code to the workflow file:

         ```yaml
      name: Select Star dbt impact report
   
      on:
        pull_request:
          types: [opened, edited, synchronize, reopened]
   
      jobs:
        create-impact-report:
          name: Create the impact report for dbt projects
          runs-on: ubuntu-latest
          permissions:
            pull-requests: write 
          steps:
            - name: Run Action
              uses: selectstar/dbt-impact-report@v1
              with:
                GIT_REPOSITORY_TOKEN: ${{secrets.GITHUB_TOKEN}}
                SELECTSTAR_API_TOKEN: ${{secrets.SELECTSTAR_API_TOKEN}}
                SELECTSTAR_API_URL: YOUR INSTANCE API URL   # (e.g.: https://api.production.selectstar.com/)
                SELECTSTAR_WEB_URL: YOUR INSTANCE WEB URL   # (e.g.: https://www.selectstar.com/)
                SELECTSTAR_DATASOURCE_GUID: YOUR DATA SOURCE GUID  # (e.g.: ds_aRjCTzAf4dPNigiV87Uggq)
         ```
      