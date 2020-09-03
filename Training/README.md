# Training models

This repo contains a GitHub Actions CI/CD workflow that you can use to automate the definition of Azure Custom Translator projects, upload of training documents, model creation and model training.

The **Data** folder in this repo contains sample data taken from the [EAC-Translation Memory](https://ec.europa.eu/jrc/en/language-technologies/eac-translation-memory) resource in the EU Science Hub - the European Commision's science and knowledge service. You should replace this sample data with your own data.

## Configuring the workflow

The workflow is defined in [.github\workflows\buildmodel.yml](../.github/workflows/buildmodel.yml). You must edit this workflow file and set the environment variables defined near the top to values that are appropriate for your solution.

### Setting environemtn variables in the workflow

```yml
env:
    # If your repository is Private, set this to true
    IS_PRIVATE_REPOSITORY: true

    # Name of the workspace that will be created
    WORKSPACE_NAME: AutomationWS

    # Root of the project names - language and short SHA will be appended
    PROJECT_NAME: EACsample

    # Custom Translator category for your documents
    # - see https://docs.microsoft.com/en-us/azure/cognitive-services/translator/custom-translator/workspace-and-project#project-categories
    PROJECT_CATEGORY: Education

    # Project description
    PROJECT_DESCRIPTION: Actions of EAC's Life-long Learning Programme (LLP) and the Youth in Action Programme

    # Languages - set this to the different language pairs that you are building for
    PROJECT_LANGUAGES: en:de|en:es|en:fr
```

### Configuring the Custom Translator CLI tool

The workflow uses the [Custom Translator CLI](https://www.nuget.org/packages/custom-translator-cli/), a CLI for the Azure Custom Translator portal services. There are a number of setup steps that you must follow carefully. Read and follow the [Azure Custom Translator CLI Installation instructions](https://github.com/AndyCW/Azure-Custom-Translator-CLI/blob/master/README.md#installation) carefully. 

In particular, note the [requirement to run the tool interactively](https://github.com/AndyCW/Azure-Custom-Translator-CLI/blob/master/README.md#using-the-cli-tool-in-a-devops-workflow) at least once ebfore you try to use it in an automation workflow.

### Setting GitHub secrets

After you have configured the CLI, you must set GitHub secrets for the Azure keys and resources such as the Azure Key Vault that you have just configured. GitHub Secrets serve as parameters to the workflow, while also hiding secret values. When viewing the logs for a workflow on GitHub, secrets will appear as `***`.

You access GitHub Secrets by clicking on the **Settings** tab on the home page of your repository, or by going to `https://github.com/{your-GitHub-Id}/{your-repository}/settings`. Then click on **Secrets** in the **Options** menu, which brings up the UI for entering Secrets.

Ensure each of the following secrets have been set, using the values for the Azure resources you have created:

| Secret Name | Value |
|-------------|-------|
| **TRANSLATOR_ACCOUNT_KEY** | Azure translator subscription key |
| **TRANSLATOR_VAULT_URI** | The DNS Name of your Azure Key Vault |
| **AZURE_CLIENT_ID** | Client ID of the Azure Active Directory application you configured |
| **AZURE_TENANT_ID** | Client ID of the Azure Active Directory application you configured |
| **AZURE_CLIENT_SECRET** | Client Secret of the Azure Active Directory application you configured |

## Running the workflow

The workflow is configured to run automatically whenever changes to files in the **\Data** folder are pushed to the master branch, for example when a Pull Request is merged.

When the workflow has completed, you can see the workflow has completed the following:

* If it did not already exist, created a new workspace with the name you set in the workflow environment variables.
* Created a new project in that workspace for each of the langauge pairs you defined in the workflow environment variables. The name is formatted as the project name you defined in the workflow environment variables with a shortened SHA hash for the run appended to it, for example: *EACsample-693ac24*.
* Uploaded all the documents found in the **.\Data\train** and **.\Data\test** folders to the workspace. The document names also have the same shortened SHA appended to identify them as belonging to this run. 
  
  > **IMPORTANT:** Documents should be named with the language pair included as a dot-delimited element in the filename. For example: **EAC_FORMS.***en_fr***.tmx**

* Created a new model in each project, using the uploaded documents for the same language pair as the project.
* Trained each model.
  