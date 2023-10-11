# Select Star dbt Impact Report

## Overview

Whenever you change your model files, the Impact Report by Select Star will create a report containing the downstream impact of those changes.

## Before you start

1. **Select Star API Token** - this is required for the Action to use Select Star's APIs. See [API Token](https://docs.selectstar.com/select-star-api/authentication).
2. **Select Star Data Source GUID** - this is the GUID of the dbt data source corresponding to the repository you're adding the Action to.
   1. You can get the GUID by going into **Admin > Data** and selecting the dbt data source. The GUID will be in the URL and look like `ds_exAmpLE`.

## Configure the GitHub Action

1. If you don't already have it, create [repository secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions) in your repo:

   1. `SELECTSTAR_API_TOKEN` with the value of the API Token from the prerequisites.

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
                GIT_REPOSITORY_TOKEN: ${{secrets.GITHUB_TOKEN}}   # no need to change, GitHub will handle it as it is
                SELECTSTAR_API_TOKEN: ${{secrets.SELECTSTAR_API_TOKEN}}
                SELECTSTAR_API_URL: YOUR INSTANCE API URL   # (e.g.: https://api.production.selectstar.com/)
                SELECTSTAR_WEB_URL: YOUR INSTANCE WEB URL   # (e.g.: https://www.selectstar.com/)
                SELECTSTAR_DATASOURCE_GUID: YOUR DATA SOURCE GUID  # (e.g.: ds_aRjCTzAf4dPNigiV87Uggq)
         ```

3. Test it Out
After configuring the GitHub action, test out the dbt Impact Report by creating a pull request with any change to a dbt
model file in the repo. You should see the action running and a new comment generated on the pull request with
the Impact report.