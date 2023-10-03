# Select Star dbt Impact Report

## Overview


## Before you start

- **Select Star API Token**: Access token to use the APIs
- **Select Star Datasource GUID**: The GUID of the datasource this repository is connected to

## Configuration

1. Create [repository secrets](https://github.com/Azure/actions-workflow-samples/blob/master/assets/create-secrets-for-GitHub-workflows.md#creating-secrets) in your repository:

   - `SELECTSTAR_API_URL` with the URL of the Select Star API instance.
   - `SELECTSTAR_WEB_URL` with the URL of the Select Star Website of the objects will be linked to.
   - `SELECTSTAR_API_TOKEN` with the value of the API access token.
   - `SELECTSTAR_DATASOURCE_GUID` with the GUID of the datasource.

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
              uses: selectstar/dbt-impact-report@v0.8
              with:
                GIT_REPOSITORY_TOKEN: ${{secrets.GITHUB_TOKEN}}
                SELECTSTAR_API_URL: ${{secrets.SELECTSTAR_API_URL}}
                SELECTSTAR_WEB_URL: ${{secrets.SELECTSTAR_WEB_URL}}
                SELECTSTAR_API_TOKEN: ${{secrets.SELECTSTAR_API_TOKEN}}
                SELECTSTAR_DATASOURCE_GUID: ${{secrets.SELECTSTAR_DATASOURCE_GUID}}
         ```