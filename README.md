# Select Star dbt Impact Report

## Overview

Whenever you change your model files, the Impact Report by Select Star will create a report containing the downstream impact of those changes.

## Before you start

- **Select Star API Token**: Access token to use the APIs
- **Select Star Datasource GUID**: The GUID of the datasource this repository is connected to

## Configuration

1. Create [repository secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) in your repository:

   - `SELECTSTAR_API_TOKEN` with the value of the API access token.

   Note: [Select Star API Token](https://docs.selectstar.com/select-star-api/authentication)

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

3. Test it out

   After completing the steps above, create a new pull request with any changes to a dbt model file to test the action.
You should see the action running and a new comment will be generated on your pull request.