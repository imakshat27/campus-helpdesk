// Local Office-file export companion to the viewer-bound presentation builder.
// Run with the bundled Node runtime and @oai/artifact-tool available via NODE_PATH
// or a node_modules link in the private build directory.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {buildDeck} from './build-deck.mjs';
const root=process.cwd();
const runtime=process.env.HELPDESK_RUNTIME_ROOT;
const skill=process.env.HELPDESK_PRESENTATIONS_SKILL;
if(!runtime||!skill) throw new Error('Set HELPDESK_RUNTIME_ROOT and HELPDESK_PRESENTATIONS_SKILL to the bundled runtime and skill directories.');
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
await buildDeck(presentation,root);
for (const [i,slide] of presentation.slides.items.entries()) {
  const preview=await presentation.export({slide,format:'png',scale:1});
  await fs.writeFile(path.join(root,'.presentation-build/final-slide-'+String(i+1).padStart(2,'0')+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
const candidatePath=path.join(root,'.presentation-build/candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const result=await finalizePresentation({
  workspaceDir:root,candidatePath,
  finalPath:path.join(root,'output/presentation/campus-helpdesk-presentation.pptx'),
  pythonExecutable:path.join(runtime,'python/bin/python3'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
  explicitTotalSlideCount:11,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
  fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
  receiptPath:path.join(root,'.presentation-build/validation.json')
});
console.log(JSON.stringify(result));
