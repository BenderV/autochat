# CHANGELOG


## v0.12.1 (2025-04-03)

### Bug Fixes

- Improve async/sync support
  ([`0dfba35`](https://github.com/BenderV/autochat/commit/0dfba35817663707969859a54e4d4d2710cbf52b))

### Documentation

- About async
  ([`27923e7`](https://github.com/BenderV/autochat/commit/27923e721b9cb336c036cb46c7552a213323f869))


## v0.12.0 (2025-04-02)

### Features

- Add async methods
  ([`28acdad`](https://github.com/BenderV/autochat/commit/28acdadcd910e2e0b37d0505598f01887fa8e43b))


## v0.11.0 (2025-03-25)

### Bug Fixes

- Bug when handling image as function response
  ([`f9c6622`](https://github.com/BenderV/autochat/commit/f9c6622f2f11cb9e4b409c6a36cd0aa1816ba00b))

- Infinite loop when handling list of strings as response...
  ([`64cefcf`](https://github.com/BenderV/autochat/commit/64cefcfa8a4b9af799a040a5cdce54c22d92a654))

### Chores

- Add capacity to have list of instance to create tools
  ([`701efae`](https://github.com/BenderV/autochat/commit/701efaebdd55870e6e394564c2d27c9c51d81420))

- Add comment
  ([`cac7e98`](https://github.com/BenderV/autochat/commit/cac7e98f9abc0fbc139597a912d94783ddfd7a5b))

- Remove self.should_pause_conversation
  ([`b05be02`](https://github.com/BenderV/autochat/commit/b05be02ebb98d293436b1fa6e954bede348d9c56))

breaking change 😨

- Remove unused version_variables
  ([`f71227f`](https://github.com/BenderV/autochat/commit/f71227fbc23048b41ddffc7aeec6b2b5670493c7))

- Update version in lock
  ([`e584ce9`](https://github.com/BenderV/autochat/commit/e584ce95eb5c3100cfa2afcc41a4ab4b42760edd))

### Features

- Add self.simple_response_callback
  ([`009acb0`](https://github.com/BenderV/autochat/commit/009acb06a7f5e39e5e2f8536036c2a360c381824))

- Add use_tools_only
  ([`2f59e26`](https://github.com/BenderV/autochat/commit/2f59e26779f74fc7c1e9a402d7f0909d423ccf84))


## v0.10.2 (2025-03-09)

### Bug Fixes

- Handle function_result if they return None
  ([`0d3b92f`](https://github.com/BenderV/autochat/commit/0d3b92f055aae2ea3240a798acd3de72f5600c35))


## v0.10.1 (2025-03-08)

### Bug Fixes

- **anthropic**: Cache bug when no content
  ([`717ca9f`](https://github.com/BenderV/autochat/commit/717ca9f4a826fac9879ab5efc53be6b655f9357b))

### Chores

- Update uv.lock
  ([`a221f18`](https://github.com/BenderV/autochat/commit/a221f1834736cbf33e2c87bff04c8a30b90daf13))


## v0.10.0 (2025-02-27)

### Features

- Rework last tools states
  ([`5e860ee`](https://github.com/BenderV/autochat/commit/5e860ee0873c1870e1ba38d97a6b82f756e9956d))


## v0.9.3 (2025-02-26)

### Bug Fixes

- Handle None return from function_call
  ([`22e348b`](https://github.com/BenderV/autochat/commit/22e348beb89f223ca4fac3224048914171f0b330))

### Chores

- Upgrade version
  ([`fb8a234`](https://github.com/BenderV/autochat/commit/fb8a23454cd99091a2392dafe475f9c06b36d653))


## v0.9.2 (2025-02-26)

### Bug Fixes

- Order of yield message
  ([`a5f42db`](https://github.com/BenderV/autochat/commit/a5f42dbd2c6c1b3784d894da82d01b9189cbf20f))


## v0.9.1 (2025-02-26)

### Bug Fixes

- Stoploopexception
  ([`8010e22`](https://github.com/BenderV/autochat/commit/8010e22004abb1627335c40329e51b08575c7600))

### Chores

- Fix test path dep
  ([`6daba02`](https://github.com/BenderV/autochat/commit/6daba025babda5840a19c2dd5939bb347eb9c638))

- Switch to sonnet 3-7 by default
  ([`4cd667e`](https://github.com/BenderV/autochat/commit/4cd667ee436230b74d166fb32d7ad09224388216))


## v0.9.0 (2025-02-24)

### Features

- Improve inspect schema
  ([`371b7c5`](https://github.com/BenderV/autochat/commit/371b7c587b9355cce9cccbeff6ea3ff7262b48b0))

support from_response and args in description


## v0.8.0 (2025-02-20)

### Features

- **dependencies**: Upgrade anthropic
  ([`dd66fc3`](https://github.com/BenderV/autochat/commit/dd66fc339aafcd49dc9da7a29c4fee980fdf4012))


## v0.7.0 (2025-02-20)

### Features

- **dependencies**: Upgrade openai
  ([`e3d1e48`](https://github.com/BenderV/autochat/commit/e3d1e483319a08f62ce8416fbc9a94b4e7907ffd))


## v0.6.0 (2025-02-20)

### Chores

- **lock**: Update
  ([`40b42cb`](https://github.com/BenderV/autochat/commit/40b42cb77db30b217b481c1fd1034ae349f958c9))

And add small CONTRIBUTE.md file

- **name**: Rename chat to agent
  ([`80580e6`](https://github.com/BenderV/autochat/commit/80580e6d0a72e6f7df528bed1ded57c5e8b1e498))

### Features

- **dependencies**: Clean lock file
  ([`46fa7ab`](https://github.com/BenderV/autochat/commit/46fa7ab522d6d77940eac14ea2eabdf4be853cdb))


## v0.5.0 (2025-01-09)

### Chores

- **clean**: Best practices
  ([`d21049f`](https://github.com/BenderV/autochat/commit/d21049f7e15ca9aaf7d3de8ae13e2f457b7847e5))

- **clean**: Refacto
  ([`90c083f`](https://github.com/BenderV/autochat/commit/90c083ff94eaac97705ba16bd8ead522d65b6b08))

- **errors**: Remove retry and error
  ([`3bfcf72`](https://github.com/BenderV/autochat/commit/3bfcf72cc014f9d24756aaea0a97e895308751d8))

- **readme**: Update example
  ([`014cdb9`](https://github.com/BenderV/autochat/commit/014cdb9c0b1966618d2967047aeb6eed53b575a3))

- **refacto**: Set providers
  ([`2ffa126`](https://github.com/BenderV/autochat/commit/2ffa126d9ced9dba529806cd063e46afb1247b2d))

- **version**: Support python 3.9
  ([`a4c67b7`](https://github.com/BenderV/autochat/commit/a4c67b7c70832e673b8bf41d13f36292049079ac))

- **workflow**: Fix workflow
  ([`5cb13d5`](https://github.com/BenderV/autochat/commit/5cb13d53d4b432cb90ba156d86f20230b3da9eca))

### Features

- **model**: Add support for function in o1
  ([`8672f20`](https://github.com/BenderV/autochat/commit/8672f20e2b4b8b72516a72432d283f76254ed851))


## v0.4.1 (2024-12-27)

### Bug Fixes

- **workflow**: Version
  ([`1413ceb`](https://github.com/BenderV/autochat/commit/1413ceb70fe93daa0902c5fca5e6b6bdce5d42a1))


## v0.4.0 (2024-12-27)

### Bug Fixes

- **worflow**: Try to fix workflow
  ([`075b54c`](https://github.com/BenderV/autochat/commit/075b54cdb8c3a7b45016bbc5297e8f98206d0b5a))

### Chores

- Bump version to 0.3.13
  ([`3d7e923`](https://github.com/BenderV/autochat/commit/3d7e9236495ba5e9e92dc947b4599c58a833e12a))

- **readme**: Add class/obj example
  ([`ff933ec`](https://github.com/BenderV/autochat/commit/ff933ecf110e5753cc29ebd408d5321563330198))

- **readme**: Add quote to pip install
  ([`78e69e5`](https://github.com/BenderV/autochat/commit/78e69e5af40ecdd413d86758e4b4027ecdfa1e67))

- **readme**: Add shields
  ([`2a6d355`](https://github.com/BenderV/autochat/commit/2a6d355e51cc8df866c47ab849ea9b57ce7337f2))

- **readme**: Fix example
  ([`8183237`](https://github.com/BenderV/autochat/commit/81832371a03a667712b2d982986fb8270b977518))

- **readme**: Improve readme
  ([`18b7c6f`](https://github.com/BenderV/autochat/commit/18b7c6f8e9ac907805335c03ece9c3d739f04441))

- **readme**: Update
  ([`c24f692`](https://github.com/BenderV/autochat/commit/c24f6929a1fec4140d07561f7cd1bc9abe9ab2f8))

- **readme**: Update default model & readme
  ([`ec83dcd`](https://github.com/BenderV/autochat/commit/ec83dcd60899b533258b7f18e4d14789bff8a194))

- **test**: Add tests
  ([`ead2683`](https://github.com/BenderV/autochat/commit/ead268326cb00bb3f30701bae6fdad44e0dc7554))

- **traceback**: Improve call adn traceback
  ([`64aca07`](https://github.com/BenderV/autochat/commit/64aca077d475618854904b50a3c0244bdf87d8e3))

- **workflow**: Fix workflow
  ([`4677f6f`](https://github.com/BenderV/autochat/commit/4677f6f1785e9977dab5c905ff986b0ce4456af9))

### Features

- **kwargs**: Allow to pass arg to openai/anthropic..
  ([`ec7fa1c`](https://github.com/BenderV/autochat/commit/ec7fa1cfb09997773939b746399800aaf2ed86da))

- **message**: Add support for parts
  ([`aa66095`](https://github.com/BenderV/autochat/commit/aa6609572fc1b68c77af7d524013a12b844238e4))

- **state**: Add reset() method
  ([`7639de0`](https://github.com/BenderV/autochat/commit/7639de0b9d25be3fade257acf69781127beedbed))

- **workflow**: Add ruff
  ([`29d90ea`](https://github.com/BenderV/autochat/commit/29d90ea3003831483fd7e51f0602e45b5f8ba999))


## v0.3.12 (2024-12-15)

### Bug Fixes

- **worflow**: Use personal token instead of github_token
  ([`82d1ebe`](https://github.com/BenderV/autochat/commit/82d1ebe692e642478e84a3215be97f55716f949c))

### Chores

- Bump version to 0.3.12
  ([`32230ed`](https://github.com/BenderV/autochat/commit/32230ed20e47f47f931eb3d60c12110d3d795d33))


## v0.3.11 (2024-12-15)

### Bug Fixes

- **worflow**: Have two step instead of one
  ([`2fba69c`](https://github.com/BenderV/autochat/commit/2fba69c7eb72c3619125ff539b50f3fc329df261))

### Chores

- Bump version to 0.3.11
  ([`c3e7063`](https://github.com/BenderV/autochat/commit/c3e7063bd9f06c2f463450cf9eaa34b623d72773))


## v0.3.10 (2024-12-15)

### Bug Fixes

- **readme**: Small fix for semantic release
  ([`5a34c1f`](https://github.com/BenderV/autochat/commit/5a34c1f6e1079143e2045b3067fe3ac9e00a77a2))

### Chores

- Bump version to 0.3.10
  ([`b77bb13`](https://github.com/BenderV/autochat/commit/b77bb1350f8b94d51bdd4590709017429eefbd45))


## v0.3.9 (2024-12-15)

### Bug Fixes

- **changelog**: Clean
  ([`4626601`](https://github.com/BenderV/autochat/commit/4626601d6473f85f66cbc374e7b8c037cecbfdd1))

- **readme**: Small fix for semantic release
  ([`1b01b09`](https://github.com/BenderV/autochat/commit/1b01b09b9fde5558a383cc0214d07971f0ba1e3f))


## v0.0.1 (2024-12-14)

### Bug Fixes

- **readme**: Small fix for semantic release
  ([`374b2f2`](https://github.com/BenderV/autochat/commit/374b2f2d3eeeb03a9165c17694057b09f9f6c709))

### Chores

- Bump version to 0.0.1
  ([`3dd6830`](https://github.com/BenderV/autochat/commit/3dd683033485364114683a8ab119f8b6413cd56e))

- **github-action**: Try to make semantic release work
  ([`b1d581d`](https://github.com/BenderV/autochat/commit/b1d581da63c0c3fcba8ebb77d01e7ddbaaf52f6c))

- **github-action**: Try to make semantic release work
  ([`9fa9b4a`](https://github.com/BenderV/autochat/commit/9fa9b4aade978d5124bc8b2ef812d8761b644ac7))


## v0.0.0 (2024-12-14)

### Chores

- Bump version to 0.0.0
  ([`19330e5`](https://github.com/BenderV/autochat/commit/19330e50479c1b4e480442d9d9bd27986411bb05))

- **deps**: Downgrade dep to avoid bug
  ([`91a5893`](https://github.com/BenderV/autochat/commit/91a589367d758c98fdbe548a8b51e31f7da79e90))

- **deps**: Update dependencies
  ([`9b6aea9`](https://github.com/BenderV/autochat/commit/9b6aea991a27d3637ac8cac94d7906cc7396af20))

- **github-action**: Adapt github actions
  ([`baf6b85`](https://github.com/BenderV/autochat/commit/baf6b85d6e319cf2cf766102f90d4a47978b570a))

- **github-action**: Adapt github actions
  ([`1bdcaf3`](https://github.com/BenderV/autochat/commit/1bdcaf36c6419bde9864d44695442932aa103b62))

- **github-action**: Adapt github actions
  ([`8cb154b`](https://github.com/BenderV/autochat/commit/8cb154bfdc1208e8438e4eebe98ada7e3905f011))

- **github-action**: Adapt github actions
  ([`ec4b555`](https://github.com/BenderV/autochat/commit/ec4b55546df2e1fb1ef2be49fc6b1d942ae57256))

- **github-action**: Fix branch to master
  ([`a367e53`](https://github.com/BenderV/autochat/commit/a367e537cc30a7f3165f53c9be881fbd8938034b))
