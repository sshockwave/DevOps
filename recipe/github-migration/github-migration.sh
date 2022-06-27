read -p "Enter the user of the repo: " repo_user
read -p "Enter the name of the repo: " repo_name
#read -p "Enter the name in the format {username}/{repo}: " repo
repo=$repo_user"/"$repo_name
read -s -p "Enter Github access token:" token

auth_header="Authorization: token "$token
accept_header="Accept: application/vnd.github.wyandotte-preview+json"

echo "Creating migration for" $repo
echo "Make sure it's not archived"

res=$(curl -H "$auth_header" -H "$accept_header" -X POST \
	-d'{"lock_repositories":true,"repositories":["'$repo'"]}' \
	https://api.github.com/user/migrations)

url=$(echo $res | \
	python3 -c "import sys,json;print(json.load(sys.stdin)['url'])")

echo "Migration URL:" $url

state=pending

while test $state != exported
do
	res=$(curl -H "$auth_header" -H "$accept_header" $url)
	state=$(echo $res | python3 -c "import sys,json;print(json.load(sys.stdin)['state'])")
	echo State: $state
done

echo Generating download URL...
curl -H "$auth_header" -H "$accept_header" $url/archive
echo

echo Unlocking Repo...
curl -H "$auth_header" -H "$accept_header" -X DELETE \
	$url/repos/$repo_name/lock
