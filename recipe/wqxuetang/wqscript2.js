function saveResToFile(url, name) {
	let btn = document.createElement('a');
	btn.download = name || '';
	btn.href = url;
	btn.click();
}
async function sleep(duration){
	return new Promise((res)=>setTimeout(res,duration));
}
async function prepare_image(node){
	let ready=null;
	let isReady=false;
	let ready_event=new Promise(res=>{ready=res;});
	if(!check()){
		node.onload=check;
		do_scroll();
	}
	return ready_event;
	function check(){
		if(isReady)return true;
		url = new URL(node.src,window.location.href);
		if(url.protocol!=='data:')return false;
		if(node.naturalHeight<1000)return false;
		isReady=true;
		ready();
		return true;
	}
	async function do_scroll(){
		while(!check()){
			node.scrollIntoView();
			if(check())break;
			await sleep(7000);
			if(check())break;
			window.scrollTo(0,0);
			await sleep(1000);
		}
	}
}
async function work(a=0,b=100000){
	let cur=Array.from(document.querySelectorAll('div[index]'));
	for(let div of cur){
		const id=Number.parseInt(div.getAttribute('index'));
		if(id<a||id>b)continue;
		const node = div.querySelector('img');
		await prepare_image(node);
		saveResToFile(node.src,`${id.toString().padStart(4, '0')}.jpg`);
		await sleep(Math.floor(Math.random()*5000));
	}
	console.log('download finished');
}
