const CONTROLLER_API = "http://localhost:8000";


const viewTitles = {

    overview: {
        title: "Overview",
        subtitle: "Hyperspace compute fabric"
    },

    nodes: {
        title: "Nodes",
        subtitle: "Machines participating in the compute mesh"
    },

    resources: {
        title: "Resources",
        subtitle: "Cluster CPU, RAM, GPU and VRAM"
    },

    jobs: {
        title: "Jobs",
        subtitle: "Compute workload management"
    },

    scheduler: {
        title: "Scheduler",
        subtitle: "Resource-aware workload placement"
    },

    execution: {
        title: "Execution",
        subtitle: "Live workload execution"
    }

};


async function getJSON(path) {

    const response =
        await fetch(
            `${CONTROLLER_API}${path}`
        );

    if (!response.ok) {

        let detail = "";

        try {

            const data =
                await response.json();

            detail =
                data.detail ||
                data.error ||
                "";

        } catch (_) {}

        throw new Error(
            detail ||
            `HTTP ${response.status}`
        );

    }

    return await response.json();

}


/* ========================= */
/* Navigation */
/* ========================= */

function showView(viewName) {

    document
        .querySelectorAll(".dashboard-view")
        .forEach(view => {

            view.classList.add("hidden");

        });


    const selectedView =
        document.getElementById(
            `view-${viewName}`
        );


    if (selectedView) {

        selectedView.classList.remove(
            "hidden"
        );

    }


    document
        .querySelectorAll(".nav-item")
        .forEach(item => {

            item.classList.toggle(
                "active",
                item.dataset.view === viewName
            );

        });


    const metadata =
        viewTitles[viewName] ||
        viewTitles.overview;


    const pageTitle =
        document.getElementById(
            "page-title"
        );

    const pageSubtitle =
        document.getElementById(
            "page-subtitle"
        );


    if (pageTitle) {
        pageTitle.textContent =
            metadata.title;
    }


    if (pageSubtitle) {
        pageSubtitle.textContent =
            metadata.subtitle;
    }


    if (viewName === "nodes") {
        loadNodes();
    }

    if (viewName === "resources") {
        loadResources();
    }

    if (viewName === "jobs") {
        loadJobs();
    }

    if (viewName === "scheduler") {
        loadScheduler();
    }

    if (viewName === "execution") {
        loadExecution();
    }

}


document
    .querySelectorAll(".nav-item")
    .forEach(item => {

        item.addEventListener(
            "click",
            () => {

                showView(
                    item.dataset.view
                );

            }
        );

    });


/* ========================= */
/* Controller status */
/* ========================= */

function setControllerStatus(online) {

    const topStatus =
        document.getElementById(
            "controller-status"
        );

    const sidebarStatus =
        document.getElementById(
            "sidebar-controller-status"
        );


    if (online) {

        if (topStatus) {
            topStatus.textContent =
                "Controller Connected";
        }

        if (sidebarStatus) {
            sidebarStatus.textContent =
                "Controller Connected";
        }

    } else {

        if (topStatus) {
            topStatus.textContent =
                "Controller Offline";
        }

        if (sidebarStatus) {
            sidebarStatus.textContent =
                "Controller Offline";
        }

    }

}


/* ========================= */
/* Overview */
/* ========================= */

async function loadOverview() {

    try {

        await getJSON(
            "/health"
        );

        setControllerStatus(
            true
        );


        const nodes =
            await getJSON(
                "/api/nodes"
            );


        const cluster =
            await getJSON(
                "/api/resources/cluster"
            );


        const nodeCount =
            document.getElementById(
                "node-count"
            );

        if (nodeCount) {
            nodeCount.textContent =
                nodes.count ?? 0;
        }


        const cpuThreads =
            document.getElementById(
                "cpu-threads"
            );

        if (cpuThreads) {
            cpuThreads.textContent =
                cluster.cpu_threads ?? 0;
        }


        const ramTotal =
            document.getElementById(
                "ram-total"
            );

        if (ramTotal) {
            ramTotal.textContent =
                `${cluster.ram_total_gb ?? 0} GB`;
        }


        const gpuCount =
            document.getElementById(
                "gpu-count"
            );

        if (gpuCount) {
            gpuCount.textContent =
                cluster.gpu_count ?? 0;
        }


        const systemStatus =
            document.getElementById(
                "system-status"
            );

        if (systemStatus) {

            systemStatus.textContent =
                "Controller API is online and cluster data is available.";

        }


    } catch (error) {

        setControllerStatus(
            false
        );


        const systemStatus =
            document.getElementById(
                "system-status"
            );


        if (systemStatus) {

            systemStatus.textContent =
                `Unable to reach controller: ${error.message}`;

        }

    }

}


/* ========================= */
/* Nodes */
/* ========================= */

function nodeStatusClass(status) {

    if (
        status &&
        String(status).toLowerCase() ===
            "online"
    ) {

        return "node-online";

    }

    return "node-offline";

}


function nodeStatusText(status) {

    if (
        status &&
        String(status).toLowerCase() ===
            "online"
    ) {

        return "ONLINE";

    }

    return "OFFLINE";

}


function renderNodes(data) {

    const container =
        document.getElementById(
            "nodes-container"
        );


    if (!container) {
        return;
    }


    const count =
        data.count ?? 0;


    const pageCount =
        document.getElementById(
            "nodes-page-count"
        );


    if (pageCount) {

        pageCount.textContent =
            count;

    }


    if (
        !data.nodes ||
        data.nodes.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                No nodes are currently registered.
            </div>
        `;

        return;

    }


    container.innerHTML =
        data.nodes
            .map(node => {

                const status =
                    nodeStatusText(
                        node.status
                    );


                const statusClass =
                    nodeStatusClass(
                        node.status
                    );


                return `
                    <article class="node-card">

                        <div class="node-card-header">

                            <div class="node-identity">

                                <div class="node-icon">
                                    H
                                </div>

                                <div>

                                    <h3>
                                        ${escapeHTML(
                                            node.hostname ||
                                            "Unknown Node"
                                        )}
                                    </h3>

                                    <span class="node-id">
                                        ${escapeHTML(
                                            node.node_id ||
                                            "Unknown ID"
                                        )}
                                    </span>

                                </div>

                            </div>


                            <div class="node-status ${statusClass}">

                                <span class="node-status-dot"></span>

                                ${status}

                            </div>

                        </div>


                        <div class="node-details">

                            <div class="node-detail">

                                <span>
                                    IP Address
                                </span>

                                <strong>
                                    ${escapeHTML(
                                        node.ip_address ||
                                        "—"
                                    )}
                                </strong>

                            </div>


                            <div class="node-detail">

                                <span>
                                    Port
                                </span>

                                <strong>
                                    ${node.port ?? "—"}
                                </strong>

                            </div>


                            <div class="node-detail">

                                <span>
                                    Platform
                                </span>

                                <strong>
                                    ${escapeHTML(
                                        node.platform ||
                                        "—"
                                    )}
                                </strong>

                            </div>


                            <div class="node-detail">

                                <span>
                                    Status
                                </span>

                                <strong>
                                    ${status}
                                </strong>

                            </div>

                        </div>

                    </article>
                `;

            })
            .join("");

}


async function loadNodes() {

    const container =
        document.getElementById(
            "nodes-container"
        );


    if (!container) {
        return;
    }


    try {

        const data =
            await getJSON(
                "/api/nodes"
            );


        renderNodes(
            data
        );

    } catch (error) {

        container.innerHTML = `
            <div class="empty-state error-state">
                Unable to load nodes:
                ${escapeHTML(
                    error.message
                )}
            </div>
        `;

    }

}


/* ========================= */
/* Resources */
/* ========================= */

function percentage(
    available,
    total
) {

    if (
        !Number.isFinite(
            Number(available)
        ) ||
        !Number.isFinite(
            Number(total)
        ) ||
        Number(total) <= 0
    ) {

        return 0;

    }


    const value =
        (
            Number(available) /
            Number(total)
        ) * 100;


    return Math.max(
        0,
        Math.min(
            100,
            value
        )
    );

}


function setResourceBar(
    elementId,
    available,
    total
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    element.style.width =
        `${percentage(
            available,
            total
        )}%`;

}


function renderClusterResources(
    cluster
) {

    const cpuTotal =
        Number(
            cluster.cpu_threads ?? 0
        );


    const ramTotal =
        Number(
            cluster.ram_total_gb ?? 0
        );


    const gpuTotal =
        Number(
            cluster.gpu_count ?? 0
        );


    const vramTotal =
        Number(
            cluster.total_vram_gb ?? 0
        );


    const cpuAvailable =
        Number(
            cluster.cpu_threads ?? 0
        );


    const ramAvailable =
        Number(
            cluster.ram_available_gb ?? 0
        );


    const gpuAvailable =
        Number(
            cluster.gpu_count ?? 0
        );


    const vramAvailable =
        Number(
            cluster.available_vram_gb ?? 0
        );


    const elements = {

        "resource-cpu-total":
            `${cpuTotal} threads`,

        "resource-cpu-available":
            `${cpuAvailable} threads`,

        "resource-ram-total":
            `${ramTotal.toFixed(2)} GB`,

        "resource-ram-available":
            `${ramAvailable.toFixed(2)} GB`,

        "resource-gpu-total":
            `${gpuTotal}`,

        "resource-gpu-available":
            `${gpuAvailable}`,

        "resource-vram-total":
            `${vramTotal.toFixed(2)} GB`,

        "resource-vram-available":
            `${vramAvailable.toFixed(2)} GB`

    };


    Object.entries(
        elements
    ).forEach(
        ([id, value]) => {

            const element =
                document.getElementById(
                    id
                );

            if (element) {
                element.textContent =
                    value;
            }

        }
    );


    setResourceBar(
        "resource-cpu-bar",
        cpuAvailable,
        cpuTotal
    );


    setResourceBar(
        "resource-ram-bar",
        ramAvailable,
        ramTotal
    );


    setResourceBar(
        "resource-gpu-bar",
        gpuAvailable,
        gpuTotal
    );


    setResourceBar(
        "resource-vram-bar",
        vramAvailable,
        vramTotal
    );

}


function renderNodeResources(
    data
) {

    const container =
        document.getElementById(
            "resource-nodes-container"
        );


    if (!container) {
        return;
    }


    const resources =
        data.resources || [];


    const count =
        document.getElementById(
            "resource-node-count"
        );


    if (count) {
        count.textContent =
            resources.length;
    }


    if (
        resources.length === 0
    ) {

        container.innerHTML = `
            <div class="empty-state">
                No resource snapshots are currently available.
            </div>
        `;

        return;

    }


    container.innerHTML =
        resources
            .map(entry => {

                const resource =
                    entry.resources || {};


                const cpu =
                    resource.cpu || {};


                const ram =
                    resource.ram || {};


                const gpus =
                    resource.gpus || [];


                const cpuThreads =
                    Number(
                        cpu.threads ??
                        cpu.cores ??
                        0
                    );


                const cpuUtilization =
                    Number(
                        cpu.utilization_percent ??
                        0
                    );


                const ramTotal =
                    Number(
                        ram.total_gb ??
                        0
                    );


                const ramAvailable =
                    Number(
                        ram.available_gb ??
                        0
                    );


                const ramUtilization =
                    Number(
                        ram.utilization_percent ??
                        0
                    );


                const totalVRAM =
                    gpus.reduce(
                        (
                            total,
                            gpu
                        ) => {

                            return total +
                                Number(
                                    gpu.vram_total_gb ??
                                    0
                                );

                        },
                        0
                    );


                const availableVRAM =
                    gpus.reduce(
                        (
                            total,
                            gpu
                        ) => {

                            return total +
                                Number(
                                    gpu.vram_available_gb ??
                                    0
                                );

                        },
                        0
                    );


                return `
                    <article class="resource-node-card">

                        <div class="resource-node-header">

                            <div class="resource-node-title">

                                <div class="node-icon">
                                    H
                                </div>

                                <div>

                                    <h3>
                                        ${escapeHTML(
                                            entry.node_id ||
                                            "Unknown Node"
                                        )}
                                    </h3>

                                    <span>
                                        Mesh ID:
                                        ${escapeHTML(
                                            entry.mesh_id ||
                                            "—"
                                        )}
                                    </span>

                                </div>

                            </div>

                        </div>


                        <div class="node-resource-grid">

                            <div class="node-resource-item">

                                <span>
                                    CPU
                                </span>

                                <strong>
                                    ${cpuThreads}
                                    threads
                                </strong>

                                <small>
                                    ${cpuUtilization.toFixed(1)}%
                                    utilization
                                </small>

                            </div>


                            <div class="node-resource-item">

                                <span>
                                    RAM
                                </span>

                                <strong>
                                    ${ramTotal.toFixed(2)}
                                    GB
                                </strong>

                                <small>
                                    ${ramAvailable.toFixed(2)}
                                    GB available ·
                                    ${ramUtilization.toFixed(1)}%
                                    used
                                </small>

                            </div>


                            <div class="node-resource-item">

                                <span>
                                    GPUs
                                </span>

                                <strong>
                                    ${gpus.length}
                                </strong>

                                <small>
                                    GPU devices
                                </small>

                            </div>


                            <div class="node-resource-item">

                                <span>
                                    VRAM
                                </span>

                                <strong>
                                    ${totalVRAM.toFixed(2)}
                                    GB
                                </strong>

                                <small>
                                    ${availableVRAM.toFixed(2)}
                                    GB available
                                </small>

                            </div>

                        </div>


                        <div class="gpu-list">

                            ${
                                gpus.length === 0
                                ? `
                                    <div class="gpu-empty">
                                        No GPU detected
                                    </div>
                                `
                                : gpus.map(gpu => {

                                    const
                                        vramTotal =
                                            Number(
                                                gpu.vram_total_gb ??
                                                0
                                            );


                                    const
                                        vramAvailable =
                                            Number(
                                                gpu.vram_available_gb ??
                                                0
                                            );


                                    const
                                        utilization =
                                            Number(
                                                gpu.utilization_percent ??
                                                0
                                            );


                                    return `
                                        <div class="gpu-row">

                                            <div>

                                                <strong>
                                                    GPU ${gpu.id ?? "—"}
                                                </strong>

                                                <span>
                                                    ${escapeHTML(
                                                        gpu.name ||
                                                        "Unknown GPU"
                                                    )}
                                                </span>

                                            </div>


                                            <div class="gpu-vram">

                                                <span>
                                                    ${vramAvailable.toFixed(2)}
                                                    /
                                                    ${vramTotal.toFixed(2)}
                                                    GB VRAM
                                                </span>

                                                <div class="gpu-bar">
                                                    <div
                                                        class="gpu-bar-fill"
                                                        style="width: ${percentage(
                                                            vramAvailable,
                                                            vramTotal
                                                        )}%"
                                                    ></div>
                                                </div>

                                            </div>


                                            <div class="gpu-utilization">
                                                ${utilization.toFixed(0)}%
                                            </div>

                                        </div>
                                    `;

                                }).join("")
                            }

                        </div>

                    </article>
                `;

            })
            .join("");

}


async function loadResources() {

    const container =
        document.getElementById(
            "resource-nodes-container"
        );


    if (!container) {
        return;
    }


    try {

        const cluster =
            await getJSON(
                "/api/resources/cluster"
            );


        const resources =
            await getJSON(
                "/api/resources"
            );


        renderClusterResources(
            cluster
        );


        renderNodeResources(
            resources
        );


    } catch (error) {

        container.innerHTML = `
            <div class="empty-state error-state">
                Unable to load resources:
                ${escapeHTML(
                    error.message
                )}
            </div>
        `;

    }

}


/* ========================= */
/* Jobs */
/* ========================= */

function jobStatusClass(status) {

    const value =
        String(status || "")
            .toLowerCase();


    if (value === "completed") {
        return "job-completed";
    }


    if (value === "running") {
        return "job-running";
    }


    if (value === "failed") {
        return "job-failed";
    }


    if (value === "cancelled") {
        return "job-cancelled";
    }


    return "job-queued";

}


function formatJobStatus(status) {

    if (!status) {
        return "UNKNOWN";
    }


    return String(status)
        .toUpperCase();

}


function renderJobs(data) {

    const container =
        document.getElementById(
            "jobs-container"
        );


    if (!container) {
        return;
    }


    const jobs =
        Array.isArray(data)
            ? data
            : (
                data.jobs ||
                data.items ||
                []
            );


    const pageCount =
        document.getElementById(
            "jobs-page-count"
        );


    if (pageCount) {

        pageCount.textContent =
            jobs.length;

    }


    if (jobs.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                No jobs are currently registered.
            </div>
        `;

        return;

    }


    container.innerHTML =
        jobs
            .map(job => {

                const status =
                    formatJobStatus(
                        job.status
                    );


                const statusClass =
                    jobStatusClass(
                        job.status
                    );


                const requirements = [];


                if (
                    job.required_cpu_threads !==
                    undefined
                ) {

                    requirements.push(
                        `${job.required_cpu_threads} CPU`
                    );

                }


                if (
                    job.required_ram_gb !==
                    undefined
                ) {

                    requirements.push(
                        `${job.required_ram_gb} GB RAM`
                    );

                }


                if (
                    job.required_gpu_count !==
                    undefined &&
                    Number(
                        job.required_gpu_count
                    ) > 0
                ) {

                    requirements.push(
                        `${job.required_gpu_count} GPU`
                    );

                }


                if (
                    job.required_vram_gb !==
                    undefined &&
                    Number(
                        job.required_vram_gb
                    ) > 0
                ) {

                    requirements.push(
                        `${job.required_vram_gb} GB VRAM`
                    );

                }


                const canCancel =
                    String(
                        job.status || ""
                    ).toLowerCase() ===
                    "queued";


                return `
                    <article class="job-card">

                        <div class="job-card-header">

                            <div class="job-identity">

                                <div class="job-icon">
                                    J
                                </div>

                                <div>

                                    <h3>
                                        ${escapeHTML(
                                            job.job_type ||
                                            "Job"
                                        )}
                                    </h3>

                                    <span class="job-id">
                                        ${escapeHTML(
                                            job.job_id ||
                                            job.id ||
                                            "Unknown ID"
                                        )}
                                    </span>

                                </div>

                            </div>


                            <div class="job-status ${statusClass}">

                                <span class="job-status-dot"></span>

                                ${status}

                            </div>

                        </div>


                        <div class="job-body">

                            <div class="job-payload">

                                <span>
                                    Payload
                                </span>

                                <strong>
                                    ${escapeHTML(
                                        job.payload?.message ||
                                        "No message"
                                    )}
                                </strong>

                            </div>


                            <div class="job-detail">

                                <span>
                                    Priority
                                </span>

                                <strong>
                                    ${job.priority ?? "—"}
                                </strong>

                            </div>


                            <div class="job-detail">

                                <span>
                                    Requirements
                                </span>

                                <strong>
                                    ${
                                        requirements.length
                                            ? escapeHTML(
                                                requirements.join(
                                                    " · "
                                                )
                                            )
                                            : "None"
                                    }
                                </strong>

                            </div>


                            ${
                                canCancel
                                    ? `
                                        <button
                                            class="secondary-button cancel-job-button"
                                            data-job-id="${escapeHTML(
                                                job.job_id ||
                                                job.id ||
                                                ""
                                            )}"
                                        >
                                            Cancel
                                        </button>
                                    `
                                    : ""
                            }

                        </div>

                    </article>
                `;

            })
            .join("");


    document
        .querySelectorAll(
            ".cancel-job-button"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    cancelJob(
                        button.dataset.jobId
                    );

                }
            );

        });

}


async function loadJobs() {

    const container =
        document.getElementById(
            "jobs-container"
        );


    if (!container) {
        return;
    }


    try {

        const data =
            await getJSON(
                "/api/jobs"
            );


        renderJobs(
            data
        );

    } catch (error) {

        container.innerHTML = `
            <div class="empty-state error-state">
                Unable to load jobs:
                ${escapeHTML(
                    error.message
                )}
            </div>
        `;

    }

}


async function cancelJob(jobId) {

    if (!jobId) {
        return;
    }


    try {

        await fetch(
            `${CONTROLLER_API}/api/jobs/${encodeURIComponent(
                jobId
            )}/cancel`,
            {
                method: "POST"
            }
        );


        await loadJobs();

    } catch (error) {

        alert(
            `Unable to cancel job: ${error.message}`
        );

    }

}


async function submitDashboardJob() {

    const messageInput =
        document.getElementById(
            "job-message"
        );


    const priorityInput =
        document.getElementById(
            "job-priority"
        );


    const status =
        document.getElementById(
            "job-submit-status"
        );


    const button =
        document.getElementById(
            "submit-job-button"
        );


    if (
        !messageInput ||
        !priorityInput ||
        !status ||
        !button
    ) {

        console.error(
            "Job submission elements not found."
        );

        return;

    }


    const message =
        messageInput.value.trim();


    const priority =
        Number(
            priorityInput.value
        );


    if (!message) {

        status.textContent =
            "Message is required.";

        return;

    }


    button.disabled = true;


    status.textContent =
        "Submitting job...";


    try {

        const response =
            await fetch(
                `${CONTROLLER_API}/api/jobs`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        job_type:
                            "test",

                        payload: {
                            message:
                                message
                        },

                        required_cpu_threads:
                            1,

                        required_ram_gb:
                            0.1,

                        required_gpu_count:
                            0,

                        required_vram_gb:
                            0,

                        priority:
                            Number.isFinite(
                                priority
                            )
                                ? priority
                                : 100

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                `HTTP ${response.status}`
            );

        }


        status.textContent =
            `Job submitted: ${
                data.job_id ||
                data.id ||
                "success"
            }`;


        await loadJobs();


        await loadScheduler();


        await loadExecution();

    } catch (error) {

        status.textContent =
            `Submission failed: ${
                error.message
            }`;

    } finally {

        button.disabled = false;

    }

}


/* ========================= */
/* Scheduler */
/* ========================= */

let schedulerJobs = [];


function populateSchedulerJobs(
    jobs
) {

    const select =
        document.getElementById("scheduler-job-select") ||
        
        document.querySelector(
            '#view-scheduler select'
        );


    schedulerJobs =
        jobs || [];


    if (!select) {

        console.error(
            "Scheduler selector not found: #scheduler-job-select"
        );

        return;

    }


    const previousValue =
        select.value;


    select.innerHTML = "";


    if (
        !jobs ||
        jobs.length === 0
    ) {

        select.innerHTML = `
            <option value="">
                No queued jobs available
            </option>
        `;

        return;

    }


    jobs.forEach(job => {

        const jobId =
            job.job_id ||
            job.id;


        if (!jobId) {
            return;
        }


        const option =
            document.createElement(
                "option"
            );


        option.value =
            jobId;


        option.textContent =
            `${job.payload?.message || job.job_type || "Job"} — ${jobId}`;


        select.appendChild(
            option
        );

    });


    if (
        previousValue &&
        [...select.options].some(
            option =>
                option.value ===
                previousValue
        )
    ) {

        select.value =
            previousValue;

    }

}


async function loadScheduler() {

    try {

        const data =
            await getJSON(
                "/api/jobs"
            );


        const jobs =
            Array.isArray(data)
                ? data
                : (
                    data.jobs ||
                    data.items ||
                    []
                );


        /*
         * Scheduler must ONLY receive queued jobs.
         * Assigned jobs must not be scheduled again.
         */
        const schedulableJobs =
            jobs.filter(job => {

                const status =
                    String(
                        job.status || ""
                    ).toLowerCase();


                return status === "queued";

            });


        populateSchedulerJobs(
            schedulableJobs
        );

    } catch (error) {

        const select =
            document.getElementById("scheduler-job-select");


        if (!select) {
            return;
        }


        select.innerHTML = `
            <option value="">
                Unable to load jobs
            </option>
        `;

    }

}


function renderAssignment(
    assignment
) {

    const container =
        document.getElementById(
            "assignment-container"
        );


    if (!container) {
        return;
    }


    if (!assignment) {

        container.innerHTML = `
            <div class="empty-state">
                No assignment returned.
            </div>
        `;

        return;

    }


    container.innerHTML = `

        <div class="assignment-card">

            <div class="assignment-header">

                <div>

                    <span class="eyebrow">
                        SCHEDULER ASSIGNMENT
                    </span>

                    <h3>
                        Node selected
                    </h3>

                </div>


                <div class="assignment-status">

                    ${escapeHTML(
                        assignment.status ||
                        "assigned"
                    ).toUpperCase()}

                </div>

            </div>


            <div class="assignment-grid">

                <div>

                    <span>
                        Job ID
                    </span>

                    <strong>
                        ${escapeHTML(
                            assignment.job_id ||
                            "—"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Node ID
                    </span>

                    <strong>
                        ${escapeHTML(
                            assignment.node_id ||
                            "—"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Scheduler Score
                    </span>

                    <strong>
                        ${assignment.score ?? "—"}
                    </strong>

                </div>


                <div>

                    <span>
                        CPU
                    </span>

                    <strong>
                        ${
                            assignment.assigned_cpu_threads ??
                            0
                        }
                        threads
                    </strong>

                </div>


                <div>

                    <span>
                        RAM
                    </span>

                    <strong>
                        ${
                            assignment.assigned_ram_gb ??
                            0
                        }
                        GB
                    </strong>

                </div>


                <div>

                    <span>
                        GPU
                    </span>

                    <strong>
                        ${
                            assignment.assigned_gpu_count ??
                            0
                        }
                    </strong>

                </div>


                <div>

                    <span>
                        VRAM
                    </span>

                    <strong>
                        ${
                            assignment.assigned_vram_gb ??
                            0
                        }
                        GB
                    </strong>

                </div>

            </div>

        </div>

    `;

}


async function scheduleSelectedJob() {

    const select =
        document.getElementById("scheduler-job-select")


    const status =
        document.getElementById(
            "scheduler-status"
        );


    const button =
        document.getElementById(
            "schedule-job-button"
        );


    if (!select) {

        console.error(
            "Scheduler selector not found."
        );

        return;

    }


    if (!status) {

        console.error(
            "Scheduler status element not found."
        );

        return;

    }


    const jobId =
        select.value;


    console.log(
        "SCHEDULER SELECTED JOB:",
        jobId
    );


    if (!jobId) {

        status.textContent =
            "Select a job first.";

        return;

    }


    if (button) {
        button.disabled = true;
    }


    status.textContent =
        "Scheduler is evaluating the resource fabric...";


    try {

        const response =
            await fetch(
                `${CONTROLLER_API}/api/scheduler/assign`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        job_id:
                            jobId
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                `HTTP ${response.status}`
            );

        }


        /*
         * Save assignment for Execution.
         */
        if (data.job_id) {

            localStorage.setItem(
                `hyperspace.assignment.${data.job_id}`,
                JSON.stringify(
                    data
                )
            );

        }


        renderAssignment(
            data
        );


        status.textContent =
            "Job successfully assigned.";


        await loadJobs();


        /*
         * Refresh scheduler so the assigned
         * job disappears from the queue.
         */
        await loadScheduler();


        /*
         * Refresh execution so the assigned
         * job becomes available there.
         */
        await loadExecution();

    } catch (error) {

        console.error(
            "Scheduling failed:",
            error
        );


        status.textContent =
            `Scheduling failed: ${
                error.message
            }`;

    } finally {

        if (button) {
            button.disabled = false;
        }

    }

}


/* ========================= */
/* Execution */
/* ========================= */

let executionJobs = [];


function populateExecutionJobs(
    jobs
) {

    const select =
        document.getElementById("execution-job-select");


    executionJobs =
        jobs || [];


    if (!select) {

        console.error(
            "Execution selector not found: #execution-job-select"
        );

        return;

    }


    /*
     * Remember what the user selected
     * before the 5-second refresh.
     */
    const previousValue =
        select.value;


    select.innerHTML = "";


    if (
        !jobs ||
        jobs.length === 0
    ) {

        const option =
            document.createElement(
                "option"
            );


        option.value = "";


        option.textContent =
            "No executable jobs available";


        select.appendChild(
            option
        );


        return;

    }


    jobs.forEach(job => {

        const jobId =
            job.job_id ||
            job.id;


        if (!jobId) {
            return;
        }


        const option =
            document.createElement(
                "option"
            );


        option.value =
            jobId;


        option.textContent =
            `${job.payload?.message || job.job_type || "Job"} — ${jobId}`;


        select.appendChild(
            option
        );

    });


    /*
     * Restore previous selection.
     */
    if (
        previousValue &&
        [...select.options].some(
            option =>
                option.value ===
                previousValue
        )
    ) {

        select.value =
            previousValue;

    }

}


async function loadExecution() {

    try {

        const data =
            await getJSON(
                "/api/jobs"
            );


        const jobs =
            Array.isArray(data)
                ? data
                : (
                    data.jobs ||
                    data.items ||
                    []
                );


        const executableJobs =
            jobs.filter(job => {

                const status =
                    String(
                        job.status || ""
                    ).toLowerCase();


                return (
                    status === "queued" ||
                    status === "assigned"
                );

            });


        populateExecutionJobs(
            executableJobs
        );


    } catch (error) {

        console.error(
            "Execution jobs loading failed:",
            error
        );


        const select =
            document.getElementById("execution-job-select")


        if (!select) {

            console.error(
                "Execution selector not found: #execution-job-select"
            );

            return;

        }


        select.innerHTML = `
            <option value="">
                Unable to load jobs
            </option>
        `;

    }

}


function renderExecutionResult(
    data
) {
    console.log(
        "FULL EXECUTION RESPONSE:",
        data
    );

    const container =
        document.getElementById(
            "execution-result-container"
        );


    if (!container) {

        console.error(
            "Execution result container not found."
        );

        return;

    }


    const result =
        data.result ||
        data;


    const success =
        result.success === true;


    const statusClass =
        success
            ? "job-completed"
            : "job-failed";


    const statusText =
        success
            ? "SUCCESS"
            : "FAILED";


    const output =
        result.output ||
        {};


    const artifact =
        data.artifact ||
        result.artifact ||
        null;


    container.innerHTML = `

        <div class="assignment-card">

            <div class="assignment-header">

                <div>

                    <span class="eyebrow">
                        EXECUTION RESULT
                    </span>

                    <h3>
                        ${statusText}
                    </h3>

                </div>


                <div
                    class="job-status ${statusClass}"
                >

                    <span
                        class="job-status-dot"
                    ></span>

                    ${statusText}

                </div>

            </div>


            <div class="assignment-grid">

                <div>

                    <span>
                        Execution ID
                    </span>

                    <strong>
                        ${escapeHTML(
                            result.execution_id ||
                            data.execution_id ||
                            "—"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Job ID
                    </span>

                    <strong>
                        ${escapeHTML(
                            result.job_id ||
                            data.job_id ||
                            "—"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Success
                    </span>

                    <strong>
                        ${success ? "YES" : "NO"}
                    </strong>

                </div>


                <div>

                    <span>
                        Artifact
                    </span>

                    <strong>
                        ${
                            artifact
                                ? escapeHTML(
                                    artifact.name ||
                                    artifact.artifact_id ||
                                    "AVAILABLE"
                                )
                                : "—"
                        }
                    </strong>

                </div>

            </div>


            <div class="execution-output">

                <span>
                    Output
                </span>

                <pre>${escapeHTML(
                    JSON.stringify(
                        output,
                        null,
                        2
                    )
                )}</pre>

            </div>


            ${
                result.error
                    ? `
                        <div class="execution-error">

                            <span>
                                Error
                            </span>

                            <pre>${escapeHTML(
                                result.error
                            )}</pre>

                        </div>
                    `
                    : ""
            }

        </div>

    `;

}


/*
 * MAIN EXECUTION FUNCTION
 *
 * Flow:
 *
 * Job
 *  ↓
 * Scheduler
 *  ↓
 * Assignment
 *  ↓
 * Node discovery
 *  ↓
 * Controller execution API
 *  ↓
 * Worker
 */
async function executeSelectedJob() {

    const select =
        document.getElementById("execution-job-select");


    if (!select) {

        console.error(
            "Execution selector not found: #execution-job-select"
        );


        alert(
            "Execution job selector not found."
        );


        return;

    }


    const jobId =
        select.value;


    console.log(
        "EXECUTION SELECTED JOB:",
        jobId
    );


    if (!jobId) {

        alert(
            "Please select a job."
        );


        return;

    }


    try {

        /*
         * Get current jobs.
         */
        const data =
            await getJSON(
                "/api/jobs"
            );


        const jobs =
            Array.isArray(data)
                ? data
                : (
                    data.jobs ||
                    data.items ||
                    []
                );


        const job =
            jobs.find(
                item =>
                    (
                        item.job_id ||
                        item.id
                    ) === jobId
            );


        if (!job) {

            throw new Error(
                "Selected job was not found."
            );

        }


        /*
         * Get scheduler assignment saved
         * by the Scheduler page.
         */
        let assignment =
            null;


        const savedAssignment =
            localStorage.getItem(
                `hyperspace.assignment.${jobId}`
            );


        if (savedAssignment) {

            try {

                assignment =
                    JSON.parse(
                        savedAssignment
                    );

            } catch (error) {

                console.warn(
                    "Invalid saved assignment. Removing it."
                );


                localStorage.removeItem(
                    `hyperspace.assignment.${jobId}`
                );

            }

        }


        /*
         * If there is no saved assignment
         * and the job is still queued,
         * schedule it automatically.
         */
        if (
            !assignment &&
            String(
                job.status || ""
            ).toLowerCase() ===
                "queued"
        ) {

            console.log(
                "No assignment found. Scheduling job..."
            );


            const scheduleResponse =
                await fetch(
                    `${CONTROLLER_API}/api/scheduler/assign`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                job_id:
                                    jobId
                            })
                    }
                );


            const scheduleData =
                await scheduleResponse.json();


            if (!scheduleResponse.ok) {

                throw new Error(
                    scheduleData.detail ||
                    scheduleData.error ||
                    `Scheduling failed: HTTP ${scheduleResponse.status}`
                );

            }


            assignment =
                scheduleData;


            localStorage.setItem(
                `hyperspace.assignment.${jobId}`,
                JSON.stringify(
                    assignment
                )
            );

        }


        /*
         * We cannot execute without
         * a scheduler assignment.
         */
        if (!assignment) {

            throw new Error(
                "No scheduler assignment found. " +
                "Run Scheduler → Find Best Node first."
            );

        }


        /*
         * Get current nodes from Controller.
         */
        const nodesData =
            await getJSON(
                "/api/nodes"
            );


        const nodes =
            Array.isArray(nodesData)
                ? nodesData
                : (
                    nodesData.nodes ||
                    nodesData.items ||
                    []
                );


        /*
         * Find the node selected by
         * the scheduler.
         */
        const node =
            nodes.find(
                item =>
                    item.node_id ===
                    assignment.node_id
            );


        if (!node) {

            throw new Error(
                `Assigned node ${assignment.node_id} was not found.`
            );

        }


        /*
         * Build the exact node object
         * expected by ControllerService.
         */
        const executionNode = {

            node_id:
                node.node_id,

            host:
                node.ip_address,

            port:
                node.port

        };


        console.log(
            "EXECUTION REQUEST:",
            {
                job_id:
                    jobId,

                assignment:
                    assignment,

                node:
                    executionNode
            }
        );


        /*
         * Send execution request.
         */
        const executionResponse =
            await fetch(
                `${CONTROLLER_API}/api/execution`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            job_id:
                                jobId,

                            assignment:
                                assignment,

                            node:
                                executionNode

                        })
                }
            );


        const executionData =
            await executionResponse.json();


        if (!executionResponse.ok) {

            throw new Error(
                executionData.detail ||
                executionData.error ||
                `Execution failed: HTTP ${executionResponse.status}`
            );

        }


        console.log(
            "EXECUTION RESULT:",
            executionData
        );


        /*
         * Display execution result.
         */
        renderExecutionResult(
            executionData
        );


        /*
         * Refresh current job state.
         */
        await loadJobs();


        await loadExecution();

    } catch (error) {

        console.error(
            "Execution failed:",
            error
        );


        alert(
            `Execution failed: ${error.message}`
        );

    }

}


/* ========================= */
/* Event listeners */
/* ========================= */

document
    .getElementById(
        "submit-job-button"
    )
    ?.addEventListener(
        "click",
        submitDashboardJob
    );


document
    .getElementById(
        "schedule-job-button"
    )
    ?.addEventListener(
        "click",
        scheduleSelectedJob
    );


document
    .getElementById(
        "execute-job-button"
    )
    ?.addEventListener(
        "click",
        executeSelectedJob
    );


/* ========================= */
/* HTML safety */
/* ========================= */

function escapeHTML(value) {

    return String(value)
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


/* ========================= */
/* Dashboard refresh */
/* ========================= */

async function refreshDashboard() {

    await loadOverview();


    const activeItem =
        document.querySelector(
            ".nav-item.active"
        );


    if (
        activeItem &&
        activeItem.dataset.view ===
            "nodes"
    ) {

        await loadNodes();

    }


    if (
        activeItem &&
        activeItem.dataset.view ===
            "resources"
    ) {

        await loadResources();

    }


    if (
        activeItem &&
        activeItem.dataset.view ===
            "jobs"
    ) {

        await loadJobs();

    }


    if (
        activeItem &&
        activeItem.dataset.view ===
            "scheduler"
    ) {

        await loadScheduler();

    }


    if (
        activeItem &&
        activeItem.dataset.view ===
            "execution"
    ) {

        await loadExecution();

    }

}


/* ========================= */
/* Initial startup */
/* ========================= */

refreshDashboard();


setInterval(
    refreshDashboard,
    5000
);





/* ========================================================= */
/* M16.9 - FAULT-TOLERANT EXECUTION                         */
/* ========================================================= */

let faultTolerantJobs = [];


/* --------------------------------------------------------- */
/* Populate fault-tolerant job selector                     */
/* --------------------------------------------------------- */

function populateFaultTolerantJobs(jobs) {

    const select =
        document.getElementById(
            "fault-tolerant-job-select"
        );


    faultTolerantJobs =
        jobs || [];


    if (!select) {

        console.error(
            "Fault-tolerant selector not found: #fault-tolerant-job-select"
        );

        return;

    }


    /*
     * Preserve the user's current selection
     * across the 5-second refresh.
     */
    const previousValue =
        select.value;


    const executableJobs =
        (jobs || []).filter(
            job => {

                const status =
                    String(
                        job.status || ""
                    ).toLowerCase();

                return (
                    status === "queued" ||
                    status === "assigned"
                );

            }
        );


    select.innerHTML = "";


    const placeholder =
        document.createElement(
            "option"
        );

    placeholder.value = "";

    placeholder.textContent =
        "Select a job";

    select.appendChild(
        placeholder
    );


    if (
        executableJobs.length === 0
    ) {

        placeholder.textContent =
            "No executable jobs";

        return;

    }


    executableJobs.forEach(
        job => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                job.job_id;


            const message =
                job.payload &&
                job.payload.message
                    ? job.payload.message
                    : job.job_id;


            option.textContent =
                `${message} — ${job.job_id}`;


            select.appendChild(
                option
            );

        }
    );


    /*
     * Restore the previous selection
     * if that job still exists.
     */
    if (
        previousValue &&
        executableJobs.some(
            job =>
                job.job_id ===
                previousValue
        )
    ) {

        select.value =
            previousValue;

    }

}


/* --------------------------------------------------------- */
/* Load jobs                                                 */
/* --------------------------------------------------------- */

async function loadFaultTolerantJobs() {

    try {

        const response =
            await fetch(
                `${CONTROLLER_API}/api/jobs`
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        populateFaultTolerantJobs(
            data.jobs || []
        );


    } catch (error) {

        console.error(
            "Fault-tolerant jobs loading failed:",
            error
        );


        const select =
            document.getElementById(
                "fault-tolerant-job-select"
            );


        if (!select) {

            return;

        }


        const previousValue =
            select.value;


        select.innerHTML = `

            <option value="">
                Unable to load jobs
            </option>

        `;


        /*
         * Do not destroy the user's selection
         * if the refresh temporarily fails.
         */
        if (previousValue) {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                previousValue;

            option.textContent =
                previousValue;

            select.appendChild(
                option
            );

            select.value =
                previousValue;

        }

    }

}


/* --------------------------------------------------------- */
/* Candidate nodes                                           */
/* --------------------------------------------------------- */

async function getFaultTolerantCandidateNodes() {

    const response =
        await fetch(
            `${CONTROLLER_API}/api/nodes`
        );


    if (!response.ok) {

        throw new Error(
            `Unable to load nodes: HTTP ${response.status}`
        );

    }


    const data =
        await response.json();


    const nodes =
        data.nodes || [];


    return nodes
        .filter(
            node =>
                String(
                    node.status || ""
                ).toLowerCase() === "online"
        )
        .map(
            node => ({

                node_id:
                    node.node_id,

                host:
                    node.ip_address,

                port:
                    node.port

            })
        );

}


/* --------------------------------------------------------- */
/* Render result                                             */
/* --------------------------------------------------------- */

function renderFaultTolerantResult(
    data
) {

    const container =
        document.getElementById(
            "fault-tolerant-result-container"
        );


    if (!container) {

        console.error(
            "Fault-tolerant result container not found."
        );

        return;

    }


    const result =
        data.result ||
        data;


    const success =
        result.success === true;


    const statusClass =
        success
            ? "job-completed"
            : "job-failed";


    const statusText =
        success
            ? "SUCCESS"
            : "FAILED";


    const output =
        result.output ||
        {};


    const artifact =
        data.artifact ||
        result.artifact ||
        null;


    container.innerHTML = `

        <div class="assignment-card">


            <div class="assignment-header">


                <div>

                    <span class="eyebrow">
                        FAULT-TOLERANT RESULT
                    </span>

                    <h3>
                        ${statusText}
                    </h3>

                </div>


                <div
                    class="job-status ${statusClass}"
                >

                    <span
                        class="job-status-dot"
                    ></span>

                    ${statusText}

                </div>


            </div>


            <div class="assignment-grid">


                <div>

                    <span>
                        Execution ID
                    </span>

                    <strong>
                        ${escapeHTML(
                            result.execution_id ||
                            "—"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Job ID
                    </span>

                    <strong>
                        ${escapeHTML(
                            result.job_id ||
                            "—"
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Success
                    </span>

                    <strong>
                        ${success
                            ? "YES"
                            : "NO"
                        }
                    </strong>

                </div>


                <div>

                    <span>
                        Artifact
                    </span>

                    <strong>
                        ${
                            artifact
                                ? escapeHTML(
                                    artifact.name ||
                                    artifact.artifact_id ||
                                    "AVAILABLE"
                                )
                                : "—"
                        }
                    </strong>

                </div>


            </div>


            <div class="execution-output">

                <span>
                    Output
                </span>

                <pre>${escapeHTML(
                    JSON.stringify(
                        output,
                        null,
                        2
                    )
                )}</pre>

            </div>


            ${
                result.error
                    ? `

                        <div class="execution-error">

                            <span>
                                Error
                            </span>

                            <pre>${escapeHTML(
                                result.error
                            )}</pre>

                        </div>

                    `
                    : ""
            }


        </div>

    `;

}


/* --------------------------------------------------------- */
/* Execute fault-tolerantly                                 */
/* --------------------------------------------------------- */

async function executeFaultTolerantly() {

    const select =
        document.getElementById(
            "fault-tolerant-job-select"
        );


    const button =
        document.getElementById(
            "fault-tolerant-execute-button"
        );


    const status =
        document.getElementById(
            "fault-tolerant-status"
        );


    if (!select) {

        console.error(
            "Fault-tolerant job selector not found."
        );

        return;

    }


    const jobId =
        select.value;


    if (!jobId) {

        if (status) {

            status.textContent =
                "Select a job first.";

        }

        return;

    }


    try {

        if (button) {

            button.disabled = true;

            button.textContent =
                "Executing...";

        }


        if (status) {

            status.textContent =
                "Discovering candidate nodes...";

        }


        const candidateNodes =
            await getFaultTolerantCandidateNodes();


        if (
            candidateNodes.length === 0
        ) {

            throw new Error(
                "No online candidate nodes are available."
            );

        }


        if (status) {

            status.textContent =
                `Executing with ${candidateNodes.length} candidate node(s)...`;

        }


        const response =
            await fetch(
                `${CONTROLLER_API}/api/execution/fault-tolerant`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        job_id:
                            jobId,

                        candidate_nodes:
                            candidateNodes

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                `HTTP ${response.status}`
            );

        }


        renderFaultTolerantResult(
            data
        );


        if (status) {

            status.textContent =
                data.success === true
                    ? "Fault-tolerant execution completed successfully."
                    : "Fault-tolerant execution failed.";

        }


    } catch (error) {

        console.error(
            "Fault-tolerant execution failed:",
            error
        );


        if (status) {

            status.textContent =
                `Execution failed: ${error.message}`;

        }


        const container =
            document.getElementById(
                "fault-tolerant-result-container"
            );


        if (container) {

            container.innerHTML = `

                <div class="empty-state">

                    Fault-tolerant execution failed.

                    <br><br>

                    ${escapeHTML(
                        error.message
                    )}

                </div>

            `;

        }

    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Execute Fault Tolerantly";

        }

    }

}


/* --------------------------------------------------------- */
/* Initialize view                                          */
/* --------------------------------------------------------- */

function initializeFaultTolerantView() {

    const button =
        document.getElementById(
            "fault-tolerant-execute-button"
        );


    if (!button) {

        return;

    }


    if (
        button.dataset.initialized === "true"
    ) {

        return;

    }


    button.dataset.initialized =
        "true";


    button.addEventListener(
        "click",
        executeFaultTolerantly
    );


    loadFaultTolerantJobs();

}


/* --------------------------------------------------------- */
/* Refresh without losing selection                          */
/* --------------------------------------------------------- */

setInterval(
    () => {

        const view =
            document.getElementById(
                "view-fault-tolerant"
            );


        if (
            view &&
            !view.classList.contains(
                "hidden"
            )
        ) {

            loadFaultTolerantJobs();

        }

    },
    5000
);


/* --------------------------------------------------------- */
/* Initialize                                               */
/* --------------------------------------------------------- */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeFaultTolerantView();

    }
);