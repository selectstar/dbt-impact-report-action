const fetchShortcut = async (path) => {
    const { default: fetch } = await import('node-fetch');
    const { SHORTCUT_API_TOKEN } = process.env
    if (!SHORTCUT_API_TOKEN) throw Error(`No environment variable: 'SHORTCUT_API_TOKEN'`)

    const response = await fetch(`https://api.app.shortcut.com/${path}`, {
        headers: {
            'Content-Type': 'application/json',
            "Shortcut-Token": SHORTCUT_API_TOKEN
        }
    });
    return response.json()
}

const fetchStory = (story_id) => fetchShortcut(`api/v3/stories/${story_id}`)
const fetchEpic = (epic_id) => fetchShortcut(`api/v3/epics/${epic_id}`)

const fetchStoryLabel = async (story_id) => {
    const story = await fetchStory(story_id);
    const labels = story.labels.map(label => label.name);
    if (story.epic_id) {
        const epic = await fetchEpic(story.epic_id)
        labels.push(...epic.labels.map(label => label.name))
    }
    return labels
}

module.exports = async ({ github, context, core, allowedLabels = [] }) => {
    const story_match = context.payload.pull_request.head.ref.match('sc-([0-9]*)')
    if (!story_match) {
        core.warning("Unable to find story ID")
        return;
    }
    const story_id = story_match[1];
    core.info(`Determined story ID: ${story_id}`)
    const story_labels = await fetchStoryLabel(story_id);
    core.info(`Story labels: ${story_labels}`);
    const new_story_labels = story_labels.filter(x => allowedLabels.includes(x));
    core.info(`Labels to add: ${new_story_labels}`)
    if (new_story_labels.length > 0) {
        await github.rest.issues.addLabels({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            labels: new_story_labels
        })
        core.info("Successfully added a new label to issue");
    } else {
        core.info("No labels to add. Skipping.")
    }
}
