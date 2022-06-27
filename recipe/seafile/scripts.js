function get_links(){
	ndlist = document.querySelectorAll('table.table-hover a.action-icon');
	ndlist = Array.from(ndlist);
	ndlist.map(x=>x.href);
	return ndlist.join('\n');
}
get_links()

async function get_parsed_links() {
	ndlist = document.querySelectorAll('table.table-hover a');
	ndlist = Array.from(ndlist);
	const ans = [];
	let domparser = new DOMParser();
	for(const lnk of ndlist) {
		console.log('fetching ', lnk.innerText);
		var iframe = document.createElement('iframe');
		iframe.src = lnk.href; 
		document.body.appendChild(iframe); // add it to wherever you need it in the document
		let video=null;
		while(video = iframe.contentDocument.querySelector('video'), !video?.src){
			await new Promise((res)=>setTimeout(res, 100));
		}
		const val = video.src;
		iframe.remove();
		delete video;
		delete iframe;
		console.log(val);
		ans.push(val);
		await new Promise((res)=>setTimeout(res, Math.random() * 5000 + 5000));
	}
	console.log('Completed!');
	console.log(ans.join('\n'));
	return ans.join('\n');
}
