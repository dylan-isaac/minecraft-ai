# Templateize and CookieCutter

Based on the project structure and its many moving parts (FastAPI, PydanticAI, dev container configuration, Docker, multiple CLI commands, and robust documentation), a layered templating strategy will give you the most flexibility, upgradeability, and composability. Here’s my take on a combined approach:

---

## 1. Use a GitHub Template Repository for the Overall Shell

**What It Provides:**

- A consistent repository “shell” that includes the high-level directory structure, all the configuration files (like the Dockerfiles, dev container files, Makefile, documentation, etc.), and the baseline code for your API and MCP server.
- Out-of-the-box support for a uniform developer experience (DX) across projects.

**Benefits:**

- **Quick Start:** Developers can click “Use this template” and immediately get an opinionated, ready-to-run environment.
- **Centralized Upgrades:** Changes to common infrastructure (like dev container settings, linting/formatting configurations, Docker Compose settings, etc.) can be applied centrally.
- **Consistent DX:** All teams or projects generated from this repository will share the same “shell” (including scripts and configuration files).

**Workflow:**

1. Enable the repository as a template on GitHub.
2. Document in the README how to customize the project after cloning (e.g., changing the project name in `pyproject.toml`, updating environment variables, etc.).
3. When creating a new project, use the GitHub template as the starting point.

---

## 2. Integrate a Cookiecutter Template for Code Scaffolding

**What It Provides:**

- A dynamic, parameterized scaffolding tool that asks for inputs (such as project name, author, target language(s), and dependency choices) and generates the inside of the project (especially the `src/` folder and related application code).
- A way to inject variables into configuration files so that each new project has its own tailored settings without manual file editing.

**Benefits:**

- **Parameterization:** Customize not only the project’s metadata but also select which pieces of code or dependencies to scaffold (e.g., choosing whether to include Node.js support in addition to Python).
- **Ease of Migration:** The templating logic can be updated over time. New versions of the Cookiecutter template can include migrations for the code inside `src/` or adjust configurations without affecting the overarching repository structure.

**Workflow:**

1. Create a `cookiecutter.json` file listing customizable variables (project name, description, preferred base images, etc.).
2. Replace hard-coded values throughout your project files (like in `pyproject.toml`, environment files, and README) with template variables.
3. When starting a new project, run:

   ```bash
   cookiecutter gh:yourusername/your-template-repo
   ```

4. Answer the prompts, and a fully parameterized project is generated.

---

## 3. Achieve Composability and Upgradability

**Composability Ideas:**

- **Modular Dev Container Configuration:**
  Design the dev container setup so that it can ingest additional templates. For example, the `.devcontainer` folder (with its Dockerfile and docker-compose settings) can be written to allow for optional base images or additional service definitions (like Node.js, Python, or others).
- **Plug-In Architecture for Dependencies:**
  Consider splitting out environment setups into modular components—such as a base Python environment, a Node.js environment, etc. Then your Cookiecutter prompts (or even a CLI tool) can allow you to compose these into the final generation. For example, if a user wants a full-stack AI app that uses both Python APIs and a Node.js frontend, your template can conditionally scaffold out the necessary directories and configuration files.
- **Centralized Updates:**
  Use versioning in your GitHub template repository. When you have updates (say, an improved Dockerfile or additional linting/formatting rules), create a new version of your template repository. For existing projects, you might consider using Git submodules or a dedicated CLI tool to help merge changes from the template into the codebase.

**Upgradability Options:**

- **CLI-Based Upgrade Script:**
  Create a command (e.g., `pat upgrade-template`) that checks for new versions of the template and optionally merges changes into an existing project.
- **Submodule or Dependency Management:**
  If there are core functionalities (for instance, the PydanticAI integrations or shared middleware) that you expect many projects to use, extract these into a separately maintained package. Then each project simply upgrades the dependency version to gain new features or fixes.

---

## 4. How the Combined Approach Looks in Practice

Imagine your final solution consists of two layers:

- **Shell (GitHub Template):**
  This contains the directory structure, environment configuration (dev container, Docker, Makefile, CI/CD workflows), and the overall DX skeleton. It sets the stage for a consistent project.
- **Core Application Code (Cookiecutter Scaffold):**
  Inside the shell, the Cookiecutter template generates the actual application code (the `src/` folder, tests, and even parts of the documentation). This part can be parameterized to include or exclude optional dependencies and can be updated independently.

**When Starting a New Project:**

1. **Use the GitHub Template:**
   Click “Use this template” on GitHub to clone the repository.
2. **Run the Cookiecutter Script:**
   Within the cloned repo, run your Cookiecutter-based CLI that scaffolds the language-specific, dependency-specific parts (or you can do this step as part of the initial generation if integrated with GitHub actions).
3. **Customize as Needed:**
   Update configuration files (such as `pyproject.toml`) and environment variables.
4. **Start Development:**
   Use the provided Make commands (like `make sync-configs`, `pat run`, and container commands) to get started immediately.

---

## Final Take

I recommend a **hybrid approach**:

- Use **GitHub Templates** to deliver a uniform "shell" that guarantees the same DX (development container, Docker configuration, linting, testing, etc.).
- Leverage **Cookiecutter** (or a similar scaffolding tool) inside that shell to generate the flexible inner project (e.g., the `src` directory) with settings tailored for each new project.
- Consider building a small CLI tool or upgrade script to help with later migrations or integrating enhancements from the upstream template into existing projects.

This approach provides:

- **Composability:** You can mix and match environments (Python, Node, etc.) and let users decide which parts to include.
- **Upgradability:** You can update the GitHub template independently from the core application code; with additional tooling, you can propagate updates or migrations.
- **Consistent DX:** Developers get a consistent out-of-the-box experience across different projects while still having the flexibility to add project-specific customizations.

Overall, this layered system will maximize reuse and maintainability while giving you the flexibility to adjust parts of the system as new requirements emerge.

Below is a detailed, step‐by‐step guide for converting your codebase into a Cookiecutter template. This approach lets you parameterize key values (for example, project name, description, Docker images, etc.) so that you or others can generate new projects with minimal effort. I’ll also explain the requirements and how you can adjust the template for environments that use Dev Containers and Docker.

---

## 1. Install Cookiecutter

The first step is to install the Cookiecutter package if you haven’t already:

```bash
pip install cookiecutter
```

Cookiecutter works with Python 3.6 and above and uses [Jinja2](https://jinja.palletsprojects.com/) templating to render your files.

---

## 2. Set Up Your Template Folder

1. **Create a new directory for the template.**
   This folder will contain your entire codebase but with some changes to allow parametrization. You might call it something like `cookiecutter-pydanticai-api-template`.

2. **Copy your entire project into this new directory.**
   Your new folder structure might look like this:

   ```text
   cookiecutter-pydanticai-api-template/
   ├── cookiecutter.json
   ├── {{ cookiecutter.project_slug }}/
       ├── .devcontainer/
       ├── .github/
       ├── docs/
       ├── examples/
       ├── promptfoo/
       ├── scripts/
       ├── src/
       ├── tests/
       ├── Dockerfile
       ├── Dockerfile.dev
       ├── docker-compose.yml
       ├── Makefile
       ├── pyproject.toml
       └── README.md
   ```

   Notice that inside the template you typically wrap all files and directories that should be renamed with a Jinja2 variable (often called `{{ cookiecutter.project_slug }}` or similar).

---

## 3. Create the `cookiecutter.json` File

At the root of your template folder (the same level as the folder that will be rendered into a project), create a file named `cookiecutter.json`. This file defines default values and variables that Cookiecutter will prompt for when a new project is generated. For example:

```json
{
  "project_name": "PydanticAI API Template",
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}",
  "description": "A template for building AI-powered APIs with PydanticAI and FastAPI.",
  "author_name": "Your Name",
  "version": "0.1.0",
  "python_version": "3.12",
  "openai_api_key": "your_openai_api_key_here",
  "docker_base_image": "python:3.12-slim"
}
```

*Notes:*

- The value for `"project_slug"` is computed dynamically from the project name.
- You can add as many variables as you need. For example, if you want to parameterize the Docker base image, include a key like `"docker_base_image"`.
- You may also add variables for environment settings that appear in your `.env` file, Dev Container config, or Docker Compose file.

---

## 4. Templatize Your Files

Now you need to go through your codebase files and replace hard-coded values with Jinja2 template variables.

### Examples

- **Project Name:**
  In your `pyproject.toml` file, replace instances of your project name with `{{ cookiecutter.project_name }}`. For example:

  ```toml
  [project]
  name = "{{ cookiecutter.project_name }}"
  version = "{{ cookiecutter.version }}"
  description = "{{ cookiecutter.description }}"
  requires-python = ">= {{ cookiecutter.python_version }}"
  ```

- **Directory Name:**
  Rename your root code folder (for example, the folder that currently might be named `pydanticai_api_template`) to:

  ```text
  {{ cookiecutter.project_slug }}
  ```

  This way, when you generate a new project, the folder gets automatically renamed.

- **Docker Files / Dev Containers:**
  In your `Dockerfile` or `.devcontainer/devcontainer.json` file, you can use variables where it makes sense. For example, in your Dockerfile, update the base image:

  ```dockerfile
  FROM {{ cookiecutter.docker_base_image }}
  ```

  And in `.devcontainer/devcontainer.json`, if your container name or forwarded ports need parametrization, you could add something like:

  ```json
  {
    "name": "{{ cookiecutter.project_name }} Dev Container",
    "workspaceFolder": "/app",
    "forwardPorts": [8000, 3001]
  }
  ```

- **Environment Files:**
  If your template should include a sample `.env` file, you can create one (say, `.env.example`) and populate it with:

  ```text
  OPENAI_API_KEY={{ cookiecutter.openai_api_key }}
  PYTHON_VERSION={{ cookiecutter.python_version }}
  ```

- **README & Documentation:**
  Replace instances of the project name or other configuration values with template variables. This way the generated README will show the correct project name.

Go through every file where the project-specific values appear and replace them with the appropriate `{{ cookiecutter.variable_name }}` notation.

---

## 5. Test the Cookiecutter Template Locally

Once you’ve updated the files:

1. **Run Cookiecutter on Your Template Locally:**
   From anywhere on your machine, run:

   ```bash
   cookiecutter /path/to/cookiecutter-pydanticai-api-template
   ```

   You’ll be prompted to input values (or you can hit enter to use the defaults). Once finished, Cookiecutter will generate a new project folder with your parameters rendered in place.

2. **Examine the Output:**
   Ensure that all the variables have been correctly replaced and that the directory structure matches what you anticipate. Test the generated project by running your setup commands, Docker commands, or launching the Dev Container.

---

## 6. Customizing for Your Environment

Depending on your needs you might want to make further changes to adjust for:

- **Dev Containers:**
  Since your template already includes a `.devcontainer` folder, you can templatize settings like forwarded ports or even specific paths. Users who generate a new project using your template can then open the project in VS Code using the “Remote - Containers” extension, and the settings you provided in the template will work out of the box.

- **Docker Setup:**
  Your `Dockerfile`, `Dockerfile.dev`, and `docker-compose.yml` can be fully templated to accept variables. For example, if you ever change the base image or encourage a new port mapping, update these files to use the corresponding cookiecutter variables.

- **Other Configuration Files:**
  Any other environment-specific or configuration files (for testing, pre-commit hooks, etc.) can be similarly modified. This ensures that once a user generates a new project from your template, they have a project already tailored for immediate use with Docker, Dev Containers, and all development tooling.

---

## 7. Publishing and Using Your Template

### Option A: Host on GitHub as a Public Template

1. **Push Your Template:**
   Create a new GitHub repository with your Cookiecutter template (for example, `cookiecutter-pydanticai-api-template`).

2. **Use It via GitHub:**
   Others (or you) can create a new project directly from it using:

   ```bash
   cookiecutter gh:yourusername/cookiecutter-pydanticai-api-template
   ```

### Option B: Keep It Locally

Simply use the local path when running Cookiecutter:

```bash
cookiecutter /path/to/cookiecutter-pydanticai-api-template
```

---

## 8. Summary of the Workflow

1. **Install Cookiecutter:**
   `pip install cookiecutter`

2. **Prepare the Template Directory:**
   Copy your repository into a new folder and rename the root project folder to `{{ cookiecutter.project_slug }}`.

3. **Create/Edit `cookiecutter.json`:**
   Define all user-configurable variables.

4. **Replace Hard-coded Values:**
   Update your source files (pyproject.toml, README.md, Dockerfiles, etc.) replacing values with `{{ cookiecutter.variable }}` expressions.

5. **Test the Template Locally:**
   Run the `cookiecutter` command against your template and adjust until the output is as expected.

6. **Publish (Optional):**
   Push to a public GitHub repository so you (and others) can generate new projects easily.

7. **Generate New Projects:**
   Use the template to quickly spin up a new AI application that comes preconfigured with Docker, Dev Containers, Makefile targets, and all other tool integrations.

---

## Additional Notes

- **Requirements:**
  – Python 3.6+
  – Git (if hosting on GitHub)
  – Cookiecutter installed via pip

- **Integration with Dev Containers and Docker:**
  Yes! Because your template is just a collection of files, you can fully templated your `.devcontainer` files and Docker configuration files. This means new projects generated from your template will automatically be set up for development with VS Code Dev Containers and Docker.

- **Documentation:**
  Make sure to include clear instructions (perhaps in a separate `template-README.md` within the template) so users know how to customize the project after generation.

By following these steps, you can turn your extensive and well-structured AI application project into a hands-on, reusable Cookiecutter template. This will help you quickly create and standardize new projects while keeping consistency across environments and deployments.
