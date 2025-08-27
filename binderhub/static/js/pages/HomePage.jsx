import { LinkGenerator } from "@jupyterhub/binderhub-react-components/LinkGenerator.jsx";
import { BuilderLauncher } from "@jupyterhub/binderhub-react-components/BuilderLauncher.jsx";
import { HowItWorks } from "@jupyterhub/binderhub-react-components/HowItWorks.jsx";
import { useEffect, useState } from "react";
import { FaviconUpdater } from "@jupyterhub/binderhub-react-components/FaviconUpdater.jsx";
import { Spec, LaunchSpec } from "@jupyterhub/binderhub-client/spec.js";

/**
 * @typedef {object} HomePageProps
 * @prop {import("../App.jsx").Provider[]} providers
 * @prop {URL} publicBaseUrl
 * @prop {URL} baseUrl
 * @param {HomePageProps} props
 */
export function HomePage({ providers, publicBaseUrl, baseUrl }) {
  const defaultProvider = providers[0];
  const [selectedProvider, setSelectedProvider] = useState(defaultProvider);
  const [repo, setRepo] = useState("");
  const [ref, setRef] = useState("");
  const [urlPath, setUrlPath] = useState("");
  const [isLaunching, setIsLaunching] = useState(false);
  const [spec, setSpec] = useState("");
  const [progressState, setProgressState] = useState(null);

  useEffect(() => {
    const encodedRepo = selectedProvider.repo.urlEncode
      ? encodeURIComponent(repo)
      : repo;
    let actualRef = "";
    if (selectedProvider.ref.enabled) {
      actualRef = ref !== "" ? ref : selectedProvider.ref.default;
    }
    setSpec(
      new Spec(
        `${selectedProvider.id}/${encodedRepo}/${actualRef}`,
        new LaunchSpec(urlPath),
      ),
    );
  }, [selectedProvider, repo, ref, urlPath]);

  return (
    <>
      <div className="text-center col-10 mx-auto">
	<img src="https://users.flatironinstitute.org/logo/blue.png" width="500px"/>
      </div>
      <div className="fw-lighter mt-8">
        <ul>
	  <li>
	    Check your <a href="/hub/hub/home">currently running server</a>.
	  </li>
	  <li>
	    <a href="https://wiki.flatironinstitute.org/Public/UsingFiBinder">Documentation</a> for users and Flatiron researchers.
	  </li>
	  <li>
	    Binder is provided as service to the community. All storage is temporary and regularly purged. <b>Do not store any sensitive or critical data.</b>
	  </li>
	</ul>
      </div>
      <LinkGenerator
        className="bg-custom-dark p-4 pb-0 rounded-top"
        publicBaseUrl={publicBaseUrl}
        providers={providers}
        selectedProvider={selectedProvider}
        setSelectedProvider={setSelectedProvider}
        repo={repo}
        setRepo={setRepo}
        reference={ref}
        setReference={setRef}
        urlPath={urlPath}
        setUrlPath={setUrlPath}
        isLaunching={isLaunching}
        setIsLaunching={setIsLaunching}
      />
      <BuilderLauncher
        className="bg-custom-dark p-4 pt-2 rounded-bottom"
        baseUrl={baseUrl}
        spec={spec}
        isLaunching={isLaunching}
        setIsLaunching={setIsLaunching}
        progressState={progressState}
        setProgressState={setProgressState}
      />
      <FaviconUpdater progressState={progressState} />
    </>
  );
}
