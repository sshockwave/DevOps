function saveResToFile(url, name) {
	let btn = document.createElement('a');
	btn.download = name || '';
	btn.href = url;
	btn.click();
}
async function sleep(duration){
	return new Promise((res)=>setTimeout(res,duration));
}
async function work(a=0,b=100000){
	let cur=Array.from(document.querySelectorAll('div[index]'));
	for(let div of cur){
		const id=Number.parseInt(div.getAttribute('index'));
		if(id<a||id>b)continue;
		const node = div.querySelector('img');
		function check(){
			url = new URL(node.src,window.location.href);
			if(url.protocol!=='data:')return false;
			if(node.naturalHeight<1000)return false;
			return true;
		}
		if(check()){
			node.scrollIntoView();
		}else{
			await sleep(Math.floor(Math.random()*5000));
			while(true){
				let isTimeout=true;
				await Promise.any([
					new Promise((res)=>{
						node.onload = ()=>{
							isTimeout=false;
							res();
						};
						node.scrollIntoView();
					}),
					sleep(7000),
				]);
				if(check())break;
				if(isTimeout){
					window.scrollTo(0,0);
					await sleep(1000);
				}
			}
		}
		saveResToFile(node.src,`${id.toString().padStart(4, '0')}.jpg`);
	}
	console.log('download finished');
}
